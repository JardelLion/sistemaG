
from rest_framework.views import APIView
from rest_framework import viewsets
from datetime import datetime
from people.models import Employee
from orders.models import Product
from orders.models import Stock, Sale, Cart, CartItem
from orders.serializers import SaleSerializer
from rest_framework.permissions import IsAuthenticated
from orders.serializers import StockManagerSerializer
from django.shortcuts import get_object_or_404
from .serializers import ProductSerializer
from .models import ProductHistory
from rest_framework.decorators import action, api_view
from .models import StockReference
from .serializers import StockReferenceSerializer
from rest_framework.viewsets import ModelViewSet

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        # Filtrar produtos apenas com stock_reference ativo
        active_stock_reference = StockReference.objects.filter(is_active=True).first()
        queryset = Product.objects.filter(stock_reference=active_stock_reference).order_by('name')
        serializer = self.get_serializer(queryset, many=True)

        # Para cada produto, adicionar quantidade e valor de aquisição
        filtered_products = []
        for product in serializer.data:
            try:
                # Obter instância do produto
                product_instance = Product.objects.get(id=product['id'])
                product_quantity = product_instance.quantity
                acquisition_value = product_instance.acquisition_value
            except Product.DoesNotExist:
                product_quantity = 0
                acquisition_value = 0.00

            filtered_products.append({
                'id': product['id'],
                'name': product['name'],
                'description': product['description'],
                'quantity': product_quantity,
                'acquisition_value': acquisition_value,
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
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Verificar se existe um stock_reference ativo
            active_stock_reference = StockReference.objects.filter(is_active=True).first()
            if not active_stock_reference:
                return Response(
                    {'error': 'No active stock reference found.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Salvar o produto e associá-lo ao estoque ativo
            product = serializer.save(stock_reference=active_stock_reference)
            data = request.data
            acquisition_value = data.get("acquisition_value")
            product_quantity = data.get('quantity', 0)  # Valor padrão: 0

            if acquisition_value is not None:
                # Criar um histórico do produto
                ProductHistory.objects.create(
                    product_id=product.id,
                    acquisition_value=acquisition_value,
                    product_quantity=product_quantity,
                    stock_reference_id=active_stock_reference.id
                )
            else:
                return Response(
                    {'error': 'Acquisition value is required.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    @action(detail=True, methods=['PUT'], url_path='update')
    def update_product(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk)
            product_history = ProductHistory.objects.get(product_id=product)
        except Product.DoesNotExist:
            return Response({'error': 'Produto não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except ProductHistory.DoesNotExist:
            product_history = ProductHistory(product_id=product)

        data = request.data
        product.name = data.get('name', product.name)
        product.price = data.get('price', product.price)
        product.description = data.get('description', product.description)
        product.quantity = (product.quantity + int(data.get('quantity', product.quantity)))
        product.acquisition_value = data.get("acquisition_value", product.acquisition_value)
        product.save()

        acquisition_value = data.get('acquisition_value')
        if acquisition_value is not None:
            product_history.acquisition_value = acquisition_value
        else:
            product_history.acquisition_value = product.acquisition_value  # Mantenha o valor atual se não houver novo

        quantity = data.get('quantity')
        if quantity is not None:
            product_history.product_quantity = (product_history.product_quantity + int(quantity))
        else:
            product_history.product_quantity = product.quantity  # Mantenha o valor atual se não houver novo

        product_history.save()
        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

class StockReferenceViewSet(ModelViewSet):
    queryset = StockReference.objects.all()
    serializer_class = StockReferenceSerializer
    
    def list(self, request, *args, **kwargs):
        queryset = self.queryset
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        instance = self.get_object()
        StockReference.objects.filter(is_active=True).update(is_active=False)
        instance.is_active = True
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @api_view(['DELETE'])
    def delete_stock(request, pk):
        try:
            # Tenta obter o registro e deletá-lo
            stock = StockReference.objects.get(pk=pk)
            stock.delete()
            return Response({'detail': f'Stock with id {pk} has been deleted.'}, status=status.HTTP_200_OK)
        except StockReference.DoesNotExist:
            return Response({'detail': f'Stock with id {pk} does not exist.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StockManagerViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockManagerSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        stock_items = Stock.objects.filter(stock_reference__is_active=True).select_related('product').order_by('product__name')
        custom_data = []
        for item in stock_items:
            custom_data.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'price': item.product.price,
                'quantity': item.quantity,
                'is_available': item.available,
                'responsible_user': item.responsible_user.name,
            })
        return Response(custom_data)
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"error": "você precisa estar autenticado para realizar esta ação."}, status=status.HTTP_403_FORBIDDEN)
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
            stock_ref = StockReference.objects.filter(is_active=True).first()
            stock = Stock.objects.get(product_id=product_id, stock_reference_id=stock_ref)
            if stock:
                return Response({"error": "O produto já está adicionado ao estoque. Use outro endpoint para ajustar a quantidade."}, status=status.HTTP_400_BAD_REQUEST)
        
        except Stock.DoesNotExist:
            pass

        # Verifica se o produto existe
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Produto não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        stock_reference = StockReference.objects.filter(is_active=True).first()

        if not stock_reference:
            return Response({"error": "Nenhum estoque ativo encontrado."}, status=status.HTTP_400_BAD_REQUEST)

        # Prepara os dados para o Stock
        stock_data = {
            'product': product.id,
            'quantity': quantity,
            'available': available,
            'description': description,
            'responsible_user': employee.id,  # O responsável é o funcionário autenticado
            'stock_reference': stock_reference.id
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
            stock_reference = StockReference.objects.filter(is_active=True).first()
            stock_item = Stock.objects.get(product_id=product_id, stock_reference_id=stock_reference)
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
            stock_reference = StockReference.objects.filter(is_active=True).first()
            stock_item = Stock.objects.get(product_id=product_id, stock_reference_id=stock_reference)
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
                notifications = Notification.objects.filter(product_description=product.description)
                
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
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            total_sales_value = 0
            total_acquisition_value = 0
            total_spend = 0

            # Itera por todas as vendas e calcula o valor total de vendas e de aquisição
            stock_reference = StockReference.objects.filter(is_active=True).first()
            sales = SaleHistory.objects.filter(stock_reference=stock_reference)

            for sale in sales:
               
                total_sales_value += sale.sale_total_value
                total_acquisition_value += (sale.sale_quantity * sale.product_acquisition_value)

            #
            # Calcula o lucro (profit) apenas se houver vendas
            if total_sales_value > 0:
                profit = total_sales_value - total_acquisition_value
                margin = (profit / total_sales_value) * 100
            else:
                profit = 0  # Se não houver vendas, o lucro é zero
                margin = 0   # E a margem também é zero

            return Response({
                "total_sales_value": total_sales_value,
                "total_acquisition_value": total_acquisition_value,
                "profit": profit,
                "margin": margin
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
        stock_reference = StockReference.objects.filter(is_active=True).first()
        product_history = ProductHistory.objects.filter(stock_reference=stock_reference)
      
        for product in product_history:
           
            if product.product_id != None:
                total_value += (product.acquisition_value * product.product_quantity)


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
        stock_reference = StockReference.objects.filter(is_active=True).first()
       

        try:
            # Verifica se o produto existe
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Produto não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Verifica se o estoque existe para o produto
            
            stock = Stock.objects.filter(product=product, stock_reference=stock_reference).first()
    
            if not stock:
                return Response({"error": "Estoque não encontrado para este produto."}, status=status.HTTP_404_NOT_FOUND)

        except Stock.DoesNotExist:
            return Response({"error": "Estoque não encontrado para este produto."}, status=status.HTTP_404_NOT_FOUND)


        try:
            # check if productHistory exist by product
            product_history = ProductHistory.objects.get(product_id=product_id)
        except ProductHistory.DoesNotExist:
            return Response({'error': "Historico de producto nao encontrado"},
                            status=status.HTTP_404_NOT_FOUND)
        
       
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
                stock_reference_id=stock_reference.id
            )

            # Diminui a quantidade no estoque
            stock.quantity -= sale_quantity
            product_history.product_quantity -= sale_quantity # take less of product_quantity reference by sell
            
            stock.save() 
            product_history.save()
            # Obtenha a instância do Employee correspondente ao request.user
            try:
                employee = Employee.objects.get(user=request.user)  # Certifique-se de que há um relacionamento entre Employee e User
            except Employee.DoesNotExist:
                return Response({"error": "Funcionário não encontrado."}, status=status.HTTP_404_NOT_FOUND)


              # Verifica se o estoque ficou abaixo de 10 e cria uma notificação
            if int(stock.quantity) < 10:
                self.create_notification(employee, product.name, product.description, stock_reference)

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

   
    def create_notification(self, employee, product_name, product_description, stock_reference):
        """Cria uma notificação quando o estoque está abaixo de 10"""
        notification_message = f"O produto '{product_name}' está abaixo de 10 unidades em estoque."
        Notification.objects.create(
            employee=employee,  # Assumindo que você tem um campo user em Notification que referencia o empregado
            message=notification_message,
            product_description=product_description,
            created_at=datetime.now(),  # Supondo que você tenha um campo 'created_at' em Notification
            stock_reference_id=stock_reference.id
        )



    
# views.py
# sales by employ with id
from rest_framework.exceptions import NotFound
from collections import defaultdict
from operator import itemgetter

class SalesByEmployeeWithIdViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, id=None):
        if id is None:
            return Response({"detail": "Employee ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=id)
        except Employee.DoesNotExist:
            raise NotFound("Funcionário não encontrado.")

        # Consulta apenas vendas não arquivadas
        sales = (
            Sale.objects
            .filter(employee=employee, is_archived=False)  # Exclui vendas arquivadas
            .select_related('product')
            .values('id', 'product__name', 'sale_quantity', 'date', 'product__price')
            .order_by("product__name")
        )

        sales_summary = defaultdict(lambda: defaultdict(lambda: {'quantity': 0, 'ids': []}))
        total_value = 0.0

        # Agrupa e calcula o total de vendas e valores
        for sale in sales:
            product_name = sale['product__name']
            sale_date = sale['date']
            sale_quantity = int(sale['sale_quantity'])
            product_price = float(sale['product__price'])
            sale_id = sale['id']

            sales_summary[product_name][sale_date]['quantity'] += sale_quantity
            sales_summary[product_name][sale_date]['ids'].append(sale_id)

            # Incrementa o valor total com base na quantidade e preço de cada venda
            total_value += product_price * sale_quantity

        sales_list = []
        for product, dates in sales_summary.items():
            for date, data in dates.items():
                # Calcula o total para cada agrupamento de produto e data
                total_product_value = sum(
                    sale['sale_quantity'] * sale['product__price'] for sale in sales if sale['product__name'] == product and sale['date'] == date
                )
                sales_list.append({
                    'product_name': product,
                    'date': date,
                    'total_quantity': data['quantity'],
                    'ids': data['ids'],
                    'total_value': total_product_value
                })

        sales_list_sorted = sorted(sales_list, key=itemgetter('date'))

        return Response({
            "employee_id": id,
            "sales": sales_list_sorted,
            'total_sales': total_value
        }, status=status.HTTP_200_OK)

class AggregateSalesByDateViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]
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
            total_sales = SaleHistory.objects.filter(employee_id=employee).annotate(
                product_pricef=F('product_price')  # Obter o preço do produto relacionado
            ).aggregate(total=Sum(F('sale_quantity') * F('product_price')))['total'] or 0

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

        # Filtra as notificações abaixo de 10
        stock_reference = StockReference.objects.filter(is_active=True).first()
        notifications = Notification.objects.filter(is_read=False, stock_reference=stock_reference)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
    
    except Employee.DoesNotExist:
        return Response({'error': 'Funcionário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
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

from django.http import HttpResponse, JsonResponse
from fpdf import FPDF
from datetime import datetime
from .models import Sale


class PDF(FPDF):
    def header(self):
        # Logotipo (substitua 'path/to/logo.png' pelo caminho do seu logotipo)
        #self.image('https://www.google.com/url?sa=i&url=https%3A%2F%2Fseekvectors.com%2Fpost%2Fimg-vector-logo&psig=AOvVaw0s2mDXYulUzs-tRKKDHHUc&ust=1736094791731000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCPidsp2_3IoDFQAAAAAdAAAAABAE', 10, 8, 33)
        # Nome da empresa
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'YourCompany', ln=True, align='R')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, '250 Executive Park Blvd, Suite 3400', ln=True, align='R')
        self.cell(0, 5, 'San Francisco CA 94134, United States', ln=True, align='R')
        self.ln(20)

    def footer(self):
        # Rodapé
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()} | YourCompany - http://www.example.com', align='C')

    def add_invoice_details(self, invoice_number, invoice_date, due_date):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f"Invoice {invoice_number}", ln=True)
        self.set_font('Arial', '', 10)
        self.cell(0, 6, f"Invoice Date: {invoice_date}", ln=True)
        self.cell(0, 6, f"Due Date: {due_date}", ln=True)
        self.ln(10)

    def add_client_details(self, client_name, client_address):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, client_name, ln=True)
        self.set_font('Arial', '', 10)
        for line in client_address:
            self.cell(0, 6, line, ln=True)
        self.ln(10)

    def add_table(self, data):
        self.set_font('Arial', 'B', 10)
        self.cell(60, 10, 'Description', border=1, align='C')
        self.cell(30, 10, 'Quantity', border=1, align='C')
        self.cell(40, 10, 'Unit Price', border=1, align='C')
        self.cell(30, 10, 'Taxes', border=1, align='C')
        self.cell(30, 10, 'Amount', border=1, align='C')
        self.ln()
        self.set_font('Arial', '', 10)

        for row in data:
            self.cell(60, 10, row['description'], border=1)
            self.cell(30, 10, str(row['quantity']), border=1, align='C')
            self.cell(40, 10, f"${row['unit_price']:.2f}", border=1, align='C')
            self.cell(30, 10, row['tax'], border=1, align='C')
            self.cell(30, 10, f"${row['amount']:.2f}", border=1, align='C')
            self.ln()

    def add_totals(self, untaxed, tax, total):
        self.ln(10)
        self.set_font('Arial', 'B', 10)
        self.cell(160, 10, 'Untaxed Amount', border=0, align='R')
        self.cell(30, 10, f"${untaxed:.2f}", border=0, align='C')
        self.ln()
        self.cell(160, 10, 'Tax 15%', border=0, align='R')
        self.cell(30, 10, f"${tax:.2f}", border=0, align='C')
        self.ln()
        self.cell(160, 10, 'Total', border=0, align='R')
        self.cell(30, 10, f"${total:.2f}", border=0, align='C')



from django.http import HttpResponse

def generate_employee_report(request):
    # Obtém os parâmetros da requisição (id do empregado e data)
    employee_id = request.GET.get('id')
    report_date = request.GET.get('date')

    try:
        # Busca os dados do histórico de vendas filtrados por empregado e data
        sales_history = SaleHistory.objects.filter(
            employee_id=employee_id,
            date=report_date
        )

        # Verifica se há vendas para gerar o relatório
        if not sales_history.exists():
            return HttpResponse(
                "Nenhum dado encontrado para o relatório.",
                status=404,
                content_type='text/plain'
            )

        # Dados do empregado (assumindo que todos têm os mesmos dados básicos)
        employee = sales_history.first().employee
        client_name = employee.name
        client_address = [employee.address]

        # Dados da venda
        sales_data = []
        for sale in sales_history:
            # Cálculo do valor total (amount) e do imposto (tax)
            amount = float(sale.product_price) * sale.sale_quantity
            tax = amount * 0.15  # 15% de imposto

            # Adiciona os dados da venda à lista de vendas
            sales_data.append({
                "description": sale.product_name,
                "quantity": sale.sale_quantity,
                "unit_price": float(sale.product_price),
                "tax": "15%",  # Exemplo de imposto fixo
                "amount": amount,
            })

        # Calcula os totais
        untaxed_amount = sum(item['amount'] for item in sales_data)
        tax_amount = untaxed_amount * 0.15
        total_amount = untaxed_amount + tax_amount

        # Gera o PDF mantendo o formato original
        pdf = PDF()
        pdf.add_page()

        # Adiciona os detalhes da fatura
        pdf.add_invoice_details(
            invoice_number=f"EMP-{employee_id}-{datetime.now().strftime('%Y%m%d')}",
            invoice_date=datetime.now().strftime('%d/%m/%Y'),
            due_date=datetime.now().strftime('%d/%m/%Y')
        )

        # Adiciona os dados do cliente
        pdf.add_client_details(client_name, client_address)

        # Adiciona os dados da tabela de vendas
        pdf.add_table(sales_data)

        # Adiciona os totais de venda
        pdf.add_totals(untaxed_amount, tax_amount, total_amount)

        # Gera o PDF e retorna como resposta
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Report-{employee_id}.pdf"'
        response['X-Status'] = 'true'  # Adiciona o cabeçalho indicando sucesso
        response.write(pdf.output(dest='S').encode('latin1'))
        return response

    except Exception as e:
        # Trata erros e adiciona o status false
        response = HttpResponse(
            f"Erro ao gerar o relatório: {str(e)}",
            status=500,
            content_type='text/plain'
        )
        response['X-Status'] = 'false'
        return response



def receipt_sale(request):
    
    sale_id = request.GET.get('sale_id')
    

    try:
        # Busca os dados do histórico de vendas filtrados por empregado e data
        sales_history = SaleHistory.objects.filter(
            sale_id=sale_id
        )

        # Verifica se há vendas para gerar o relatório
        if not sales_history.exists():
            return HttpResponse(
                "Nenhum dado encontrado para o relatório.",
                status=404,
                content_type='text/plain'
            )

        # Dados do empregado (assumindo que todos têm os mesmos dados básicos)
        employee = sales_history.first().employee
        client_name = employee.name
        client_address = [employee.address]

        # Dados da venda
        sales_data = []
        for sale in sales_history:
            # Cálculo do valor total (amount) e do imposto (tax)
            amount = float(sale.product_price) * sale.sale_quantity
            tax = amount * 0.15  # 15% de imposto

            # Adiciona os dados da venda à lista de vendas
            sales_data.append({
                "description": sale.product_name,
                "quantity": sale.sale_quantity,
                "unit_price": float(sale.product_price),
                "tax": "15%",  # Exemplo de imposto fixo
                "amount": amount,
            })

        # Calcula os totais
        untaxed_amount = sum(item['amount'] for item in sales_data)
        tax_amount = untaxed_amount * 0.15
        total_amount = untaxed_amount + tax_amount

        # Gera o PDF mantendo o formato original
        pdf = PDF()
        pdf.add_page()

        # Adiciona os detalhes da fatura
        pdf.add_invoice_details(
            invoice_number=f"EMP-{sale_id}-{datetime.now().strftime('%Y%m%d')}",
            invoice_date=datetime.now().strftime('%d/%m/%Y'),
            due_date=datetime.now().strftime('%d/%m/%Y')
        )

        # Adiciona os dados do cliente
        pdf.add_client_details(client_name, client_address)

        # Adiciona os dados da tabela de vendas
        pdf.add_table(sales_data)

        # Adiciona os totais de venda
        pdf.add_totals(untaxed_amount, tax_amount, total_amount)

        # Gera o PDF e retorna como resposta
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Report-{sale_id}.pdf"'
        response['X-Status'] = 'true'  # Adiciona o cabeçalho indicando sucesso
        response.write(pdf.output(dest='S').encode('latin1'))
        return response

    except Exception as e:
        # Trata erros e adiciona o status false
        response = HttpResponse(
            f"Erro ao gerar o relatório: {str(e)}",
            status=500,
            content_type='text/plain'
        )
        response['X-Status'] = 'false'
        return response


class UpdateEmployeeSector(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, employee_id):
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Funcionário não encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        sector_id = request.data.get('sector')  # Recebendo o ID do setor

        if not sector_id:
            return Response({"error": "O ID do setor é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Buscando o StockReference correspondente ao setor
            sector = StockReference.objects.get(id=sector_id)
        except StockReference.DoesNotExist:
            return Response({"error": "Setor não encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        # Atualizando o campo stock_reference do funcionário
        employee.stock_reference = sector
        employee.save()

        return Response({
            "message": f"Setor do funcionário {employee_id} atualizado para: {sector.name}"
        }, status=status.HTTP_200_OK)