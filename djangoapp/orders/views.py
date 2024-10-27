from django.db.models import Sum, F
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication

from datetime import datetime
from people.models import Employee
from orders.models import Product
from orders.models import Stock, Sale, Cart, CartItem
from orders.serializers import SaleSerializer

from rest_framework.permissions import IsAuthenticated
from orders.serializers import StockManagerSerializer
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from .serializers import ProductSerializer
from .models import ProductHistory, Notification


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Para cada produto, buscar a quantidade no próprio produto e o valor de aquisição
        filtered_products = []
        for product in serializer.data:
            try:
                # Aqui estamos pegando a quantidade do próprio produto
                product_instance = Product.objects.get(id=product['id'])
                product_quantity = product_instance.quantity  # Quantidade no próprio produto
                acquisition_value = product_instance.acquisition_value  # Valor de aquisição do produto
            except Product.DoesNotExist:
                product_quantity = 0  # Caso o produto não tenha uma quantidade definida
                acquisition_value = 0.00  # Valor de aquisição padrão

            filtered_products.append({
                'id': product['id'],
                'name': product['name'],
                'description': product['description'],
                'quantity': product_quantity,  # Quantidade no próprio produto
                'acquisition_value': acquisition_value,  # Valor de aquisição
                'price': product['price']
            })

        return Response(filtered_products)
    
     # Desabilitar os métodos padrão de criação, atualização e deleção
    def create(self, request, *args, **kwargs):
        return Response({'error': 'Método não permitido.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response({'error': 'Método não permitido.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    @action(detail=False, methods=['post'], url_path='create')
    def create_product(self, request):
       
        
        # Serialização dos dados da requisição
        serializer = self.get_serializer(data=request.data)
        
        # Verificar se os dados são válidos
        if serializer.is_valid():
            # Salvar o produto após validação
            product = serializer.save()
            
            # Capturar os dados da requisição
            data = request.data
            
            # Verificar se o campo 'acquisition_value' está presente
            acquisition_value = data.get("acquisition_value")
            if acquisition_value is not None:
                # Criar o histórico do produto
                ProductHistory.objects.create(
                    product_id=product.id,  # Usar a instância do produto
                    acquisition_value=acquisition_value  # Valor de aquisição vindo da requisição
                )
            else:
                return Response({'error': 'Acquisition value is required.'}, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['PUT'], url_path='update')
    def update_product(self, request, pk=None):
        try:
            # Recupera o produto usando o pk fornecido
            product = Product.objects.get(pk=pk)
            
            # Tenta recuperar o histórico do produto, se existir
            product_history = ProductHistory.objects.get(product_id=product)

        except Product.DoesNotExist:
            return Response({'error': 'Produto não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except ProductHistory.DoesNotExist:
            # Se não houver histórico, criamos um novo
            product_history = ProductHistory(product_id=product)

        # Atualize os dados do produto
        data = request.data
        product.name = data.get('name', product.name)
        product.price = data.get('price', product.price)
        product.quantity = data.get('quantity', product.quantity)
        product.acquisition_value = data.get("acquisition_value", product.acquisition_value)

        # Salva as alterações no produto
        product.save()

        # Atualiza o valor de aquisição no histórico
        acquisition_value = data.get('acquisition_value')
        if acquisition_value is not None:
            product_history.acquisition_value = acquisition_value
        else:
            product_history.acquisition_value = product.acquisition_value  # Mantenha o valor atual se não houver novo

        # Salva as alterações no histórico
        product_history.save()

        # Serializa e retorna os dados do produto atualizado
        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)



   

class StockManagerViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockManagerSerializer
    #permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        # Obtém todos os objetos de Stock
        stock_items = self.get_queryset()

        # Cria uma lista personalizada com os detalhes que deseja retornar
        custom_data = []
        for item in stock_items:
            custom_data.append({
                'product_id': item.product.id,
                'product_name': item.product.name,  # Acessa o nome do produto
                'price': item.product.price,
                'quantity': item.quantity,
                'is_available': item.available,  # Quantidade no estoque
                'responsible_user': item.responsible_user.name,  # Acessa o nome do responsável
            })

        # Retorna a resposta com os dados customizados
        return Response(custom_data)

    def create(self, request, *args, **kwargs):
        # Verifica se o usuário está autenticado
        if not request.user.is_authenticated:
            return Response({"error": "você precisa estar autenticado para realizar esta ação."}, status=status.HTTP_403_FORBIDDEN)

        # Obtém o funcionário associado ao usuário autenticado
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response({"error": "Funcionário não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        employee = Employee.objects.get(user=request.user)
        # Coleta os dados da requisição
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity'))
        description = request.data.get('description', '')
        available = request.data.get('is_available')

        # Verifica se o produto já está no estoque
        try:
            stock = Stock.objects.get(product_id=product_id)
            return Response({"error": "O produto já está adicionado ao estoque. Use outro endpoint para ajustar a quantidade."}, status=status.HTTP_400_BAD_REQUEST)
        except Stock.DoesNotExist:
            pass

        # Verifica se o produto existe
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Produto não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # Prepara os dados para o Stock
        stock_data = {
            'product': product.id,
            'quantity': quantity,
            'available': available,
            'description': description,
            'responsible_user': employee.id,  # O responsável é o funcionário autenticado
        }

        # Serializa os dados
        serializer = self.get_serializer(data=stock_data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        # Obtém o ID do produto a ser excluído
        product_id = kwargs.get('pk')

        # Tenta obter o objeto de estoque relacionado ao produto
        try:
            stock_item = Stock.objects.get(product_id=product_id)
        except Stock.DoesNotExist:
            return Response({"error": "Produto não encontrado no estoque."}, status=status.HTTP_404_NOT_FOUND)

        quantity_to_return = stock_item.quantity
        # Remove o item do estoque
        stock_item.delete()

        try:
            product = Product.objects.get(id=product_id)
            product.quantity += quantity_to_return
            product.save()
        
        except Product.DoesNotExist:
            return Response({"error": "Produto não encontrado"}, status=status.HTTP_404_NOT_FOUND)


        return Response(status=status.HTTP_204_NO_CONTENT)




    def update(self, request, *args, **kwargs):
        # Obtém o ID do produto para atualização
        product_id = kwargs.get('pk')

        # Tenta obter o item de estoque existente
        try:
            stock_item = Stock.objects.get(product_id=product_id)
        except Stock.DoesNotExist:
            return Response({"error": "Produto não encontrado no estoque."}, status=status.HTTP_404_NOT_FOUND)

        # Tenta obter o produto relacionado ao item de estoque
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Produto não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # Coleta a quantidade a ser adicionada ao estoque
        new_quantity = int(request.data.get('quantity'))
        if new_quantity is None:
            return Response({"error": "Quantidade não fornecida."}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica se a quantidade solicitada é maior do que a disponível no produto
        if new_quantity > product.quantity:
            return Response({"error": "A quantidade solicitada é maior do que a disponível no produto."}, status=status.HTTP_400_BAD_REQUEST)

        # Subtrai a quantidade do produto e adiciona ao estoque
        product.quantity -= new_quantity
        product.save()

        stock_item.quantity += new_quantity
        stock_item.save()

        if int(stock_item.quantity) > 10:
            try:
                # Filtra notificações pelo `product_id`
                notifications = Notification.objects.filter(product_id=product)
                
                if not notifications.exists():
                    return Response({"error": "O produto não foi notificado"}, status=status.HTTP_400_BAD_REQUEST)

                # Atualiza o campo `is_read` de cada notificação e salva
                for notification in notifications:
                    notification.is_read = True
                    notification.save()

            except Notification.DoesNotExist:
                return Response({"error": "O produto não foi notificado"}, status=status.HTTP_400_BAD_REQUEST)


       
        # Serializa os dados atualizados
        serializer = self.get_serializer(stock_item)

        return Response(serializer.data, status=status.HTTP_200_OK)

from .models import SaleHistory
class TotalSalesAndAcquisitionValueView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            total_sales_value = 0
            total_acquisition_value = 0
            total_spend = 0

            # Itera por todas as vendas e calcula o valor total de vendas e de aquisição
            sales = SaleHistory.objects.all()
            for sale in sales:
               
                total_sales_value += sale.sale_quantity * sale.product_price
                total_acquisition_value += sale.sale_quantity * sale.product_acquisition_value

            # Calcula o total de custos de aquisição de todos os produtos
            products = ProductHistory.objects.all()
            for product in products:
                total_spend += product.acquisition_value

            # Calcula o lucro (profit) apenas se houver vendas
            if total_sales_value > 0:
                profit = total_sales_value - total_spend
                margin = (profit / total_sales_value) * 100
            else:
                profit = 0  # Se não houver vendas, o lucro é zero
                margin = 0   # E a margem também é zero

            return Response({
                "total_sales_value": total_sales_value,
                "total_acquisition_value": total_acquisition_value,
                "profit": profit,
                "margin": margin,
                'total_spend': total_spend
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import views

class TotalProductValueView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna o valor total de todos os produtos em estoque"""
        total_value = 0
        
        # Itera sobre todos os itens no estoque
        product_history = ProductHistory.objects.all()
        for product in product_history:
            total_value += product.acquisition_value


        return Response({
            "total_stock_value": (total_value)
        }, status=status.HTTP_200_OK)




class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]


    def create(self, request, *args, **kwargs):
        employee_id = request.data.get("employee")
        product_id = request.data.get("product")
        sale_quantity = int(request.data.get("sale_quantity"))
       

        try:
            # Verifica se o produto existe
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Produto não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Verifica se o estoque existe para o produto
            stock = Stock.objects.get(product=product)
        except Stock.DoesNotExist:
            return Response({"error": "Estoque não encontrado para este produto."}, status=status.HTTP_404_NOT_FOUND)


        # Verifica se o produto está disponível
        if not stock.available:
            return Response({"error": f"O produto {product.name} não está disponível para venda."}, status=status.HTTP_400_BAD_REQUEST)


        # Verifica se a quantidade de venda é válida
        if int(sale_quantity) > int(stock.quantity):
            return Response({"error": "A quantidade vendida excede o estoque disponível."}, status=status.HTTP_400_BAD_REQUEST)

        # Aqui você pode criar a venda
        try:
            sale = Sale.objects.create(
                employee_id=employee_id,
                product=product,
                sale_quantity=sale_quantity,
            )

            # Diminui a quantidade no estoque
            stock.quantity -= sale_quantity
            stock.save() 
            
            # Obtenha a instância do Employee correspondente ao request.user
            try:
                employee = Employee.objects.get(user=request.user)  # Certifique-se de que há um relacionamento entre Employee e User
            except Employee.DoesNotExist:
                return Response({"error": "Funcionário não encontrado."}, status=status.HTTP_404_NOT_FOUND)


              # Verifica se o estoque ficou abaixo de 10 e cria uma notificação
            if int(stock.quantity) < 10:
                self.create_notification(employee, product.name)

            self.clear_cart(request)

            return Response({
                "message": "Venda realizada com sucesso.",
                "sale_id": sale.id
            }, status=status.HTTP_201_CREATED)
        
            

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



    def clear_cart(self, request):
        """Esvazia o carrinho do usuário"""
        cart = Cart.objects.get(user=request.user)
        CartItem.objects.filter(cart=cart).delete()
        return Response({'message': 'Carrinho esvaziado com sucesso'}, status=status.HTTP_200_OK)

   
    def create_notification(self, employee, product_name):
        """Cria uma notificação quando o estoque está abaixo de 10"""
        notification_message = f"O produto '{product_name}' está abaixo de 10 unidades em estoque."
        Notification.objects.create(
            employee=employee,  # Assumindo que você tem um campo user em Notification que referencia o empregado
            message=notification_message,
            created_at=datetime.now()  # Supondo que você tenha um campo 'created_at' em Notification
        )



    
# views.py
# sales by employ with id
from rest_framework.exceptions import NotFound
from collections import defaultdict
from operator import itemgetter

class SalesByEmployeeWithIdViewSet(viewsets.ViewSet):
    # permission_classes = [IsAuthenticated]

    def list(self, request, id=None):
        # Se o ID do funcionário não for fornecido, retorne um erro
        if id is None:
            return Response({"detail": "Employee ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Tenta obter o funcionário pelo ID
            employee = Employee.objects.get(id=id)
        except Employee.DoesNotExist:
            raise NotFound("Funcionário não encontrado.")

        # Consulta as vendas associadas ao funcionário
        sales = (
            Sale.objects
            .filter(employee=employee)  # Filtra vendas pelo funcionário
            .select_related('product')   # Assume que há uma relação com Product
            .values(
                'id',  # ID da venda
                'product__name',  # Nome do produto
                'sale_quantity',  # Quantidade vendida
                'date',  # Data da venda
                'product__price'
            )
        )

        # Dicionário para agrupar as vendas por produto e data
        sales_summary = defaultdict(lambda: defaultdict(lambda: {'quantity': 0, 'ids': []}))  
        total_value = 0.0

        # Itera pelas vendas e agrupa por produto e data
        for sale in sales:
            product_name = sale['product__name']
            sale_date = sale['date']
            sale_quantity = int(sale['sale_quantity'])
            product_price = float(sale['product__price'])
            sale_id = sale['id']

            # Agrupa por produto e data, somando as quantidades e armazenando os IDs
            sales_summary[product_name][sale_date]['quantity'] += sale_quantity
            sales_summary[product_name][sale_date]['ids'].append(sale_id)

            # Calcula o valor total da venda
            total_value += product_price * sale_quantity

        # Montar a lista final de vendas agrupadas por produto e data, incluindo os IDs
        sales_list = []
        for product, dates in sales_summary.items():
            for date, data in dates.items():
                sales_list.append({
                    'product_name': product,
                    'date': date,
                    'total_quantity': data['quantity'],
                    'ids': data['ids'],  # Inclui a lista de IDs
                    'total_value': data['quantity'] * product_price  # Valor total por produto
                })

        # Ordenar a lista de vendas pela data, do menor para o maior
        sales_list_sorted = sorted(sales_list, key=itemgetter('date'))

        # Retorna as vendas agrupadas como resposta
        return Response({"employee_id": id, "sales": sales_list_sorted, 'total_sales': total_value}, status=status.HTTP_200_OK)

class AggregateSalesByDateViewSet(viewsets.ViewSet):
    #permission_classes = [IsAuthenticated]

    def list(self, request):
        sales = (
            Sale.objects
            .select_related('product')
            .values('date')
            .annotate(
                total_sales=Sum(F('sale_quantity') * F('product__price')),
                total_quantity=Sum('sale_quantity')
            )
        )
        return Response(list(sales))
    

from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db.models import Sum, F


class SalesByEmployee(viewsets.ViewSet):
    """
    ViewSet para retornar o total de vendas por funcionário.
    """

    def list(self, request):
        # Obtém todos os funcionários
        employees = Employee.objects.filter(role='employee')

        # Cria uma lista para armazenar os dados de vendas por funcionário
        sales_data = []
        
        for employee in employees:
            # Calcula o total de vendas para cada funcionário
            total_sales = Sale.objects.filter(employee=employee).annotate(
                product_price=F('product__price')  # Obter o preço do produto relacionado
            ).aggregate(total=Sum(F('sale_quantity') * F('product__price')))['total'] or 0

            sales_data.append({
                'employee_id': employee.id,
                'employee_name': employee.name,
                'total_sales': total_sales
            })

        return Response(sales_data, status=status.HTTP_200_OK)


from rest_framework.views import APIView

class CartItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        try:
            # 1. Obter o usuário a partir do employee_id
            employee = Employee.objects.get(id=employee_id)
            user = employee.user
            
            # 2. Obter o carrinho do usuário
            cart = Cart.objects.get(user=user)
            
            # 3. Obter os itens do carrinho
            cart_items = CartItem.objects.filter(cart=cart)

            # 4. Serializar os dados
            serialized_items = [
                {
                    'product_id': item.product.id,
                    'quantity': item.quantity,
                    'product_name': item.product.name,
                    "product_price": item.product.price  # Supondo que o produto tenha um nome
                    # Adicione mais campos conforme necessário
                }
                for item in cart_items
            ]

            return Response(serialized_items, status=status.HTTP_200_OK)

        except Employee.DoesNotExist:
            return Response({"error": "Funcionário não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Cart.DoesNotExist:
            return Response({"error": "Carrinho não encontrado."}, status=status.HTTP_404_NOT_FOUND)


from .serializers import CartSerializer
class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Retorna o carrinho do usuário"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='add')
    def add_to_cart(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity'))  # Garantindo que a quantidade seja um número inteiro

        try:
            # Verificar se o produto existe
            product = Product.objects.get(id=product_id)

            # Obter a quantidade disponível do produto no estoque usando StockManager
            stock_manager_entry = Stock.objects.filter(product=product).first()
            if stock_manager_entry is None:
                return Response({"error": "Produto não está disponível em estoque."}, status=status.HTTP_404_NOT_FOUND)

            
             # Verificar se o produto está disponível
            if not stock_manager_entry.available:
                return Response({"error": "Produto não está disponível para adicionar ao carrinho."}, status=status.HTTP_400_BAD_REQUEST)

            
            available_quantity = stock_manager_entry.quantity  # Aqui estamos pegando a quantidade do estoque

            # Verificar se a quantidade é válida
            if quantity > available_quantity:
                return Response({"error": "A quantidade solicitada excede o estoque disponível."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Obter ou criar o carrinho do usuário
            cart, created = Cart.objects.get_or_create(user=request.user)

            # Verificar se o produto já está no carrinho
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})

            if not created:
                # Se o item já está no carrinho, apenas incrementar a quantidade
                new_quantity = cart_item.quantity + quantity
                if new_quantity > available_quantity:
                    return Response({"error": "A quantidade total excede o estoque disponível."}, status=status.HTTP_400_BAD_REQUEST)
                cart_item.quantity = new_quantity
                cart_item.save()

            return Response({
                "message": "Produto adicionado ao carrinho com sucesso.",
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "quantity": cart_item.quantity,
                    "price": product.price
                }
            }, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response({"error": "Produto não encontrado."}, status=status.HTTP_404_NOT_FOUND)

    def remove_from_cart(self, request, pk):
        """Remove um item do carrinho"""
        cart = Cart.objects.get(user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, id=pk)
        cart_item.delete()

        return Response({'message': 'Produto removido do carrinho'}, status=status.HTTP_204_NO_CONTENT)





from rest_framework.decorators import api_view
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.decorators import permission_classes

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_notifications(request):
    if not request.user.is_authenticated:
        return Response({
            'error': "Usuário não autenticado."
        }, status=status.HTTP_401_UNAUTHORIZED)
    try:
        # Busca o funcionário associado ao usuário
        #employee = Employee.objects.get(user=request.user)

        # Filtra as notificações abaixo de 10
        notifications = Notification.objects.filter(is_read=False)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
    
    except Employee.DoesNotExist:
        return Response({'error': 'Funcionário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
def mark_as_read(request, notification_id):
    try:
        employee = Employee.objects.get(user=request.user)
        notification = Notification.objects.get(id=notification_id, 
                                                employee=employee)
    except Notification.DoesNotExist:
        return Response({
            'error': "Notificação não encontrada."
        }, status=status.HTTP_404_NOT_FOUND)
    
    notification.is_read = True 
    notification.save()
    serializer = NotificationSerializer(notification)
    return Response(serializer.data)
