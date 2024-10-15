from django.shortcuts import render
from django.db.models import Sum, F
from rest_framework.response import Response
from rest_framework import views
from django.contrib.postgres.aggregates import ArrayAgg
from rest_framework.views import APIView
from rest_framework import viewsets, generics, status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.authentication import TokenAuthentication
import locale

from .models import Employee, Product, Stock, Sale, ActionHistory
from .serializers import (
    EmployeeSerializer,
    ProductSerializer,
    StockManagerSerializer,
    SaleSerializer,
    ActionHistorySerializer,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.decorators import action


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    #permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Para cada produto, buscar a quantidade no estoque associado
        filtered_products = []
        for product in serializer.data:
            try:
                stock = Stock.objects.get(product_id=product['id'])  # Busca a quantidade no estoque
                stock_quantity = stock.quantity
            except Stock.DoesNotExist:
                stock_quantity = 0  # Caso o produto não tenha um registro de estoque, assume 0

            filtered_products.append({
                'id': product['id'],
                'name': product['name'],
                'stock_quantity': stock_quantity,  # Quantidade no estoque
                'price': product['price']
            })

        return Response(filtered_products)

    @action(detail=False, methods=['post'], url_path='create')
    def create_product(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['PUT'], url_path='update')
    def update_product(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({
                'error': 'Produto não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        product.name = data.get('name', product.name)
        product.price = data.get('price', product.price)

        product.save()

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
                'quantity': item.quantity,  # Quantidade no estoque
                'acquisition_value': item.acquisition_value,
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
        quantity = request.data.get('quantity')
        acquisition_value = request.data.get('acquisition_value', 0)
        description = request.data.get('description', '')

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
            'acquisition_value': acquisition_value,
            'description': description,
            'responsible_user': employee.id,  # O responsável é o funcionário autenticado
        }

        # Serializa os dados
        serializer = self.get_serializer(data=stock_data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class TotalStockValueView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna o valor total de todos os produtos em estoque"""
        total_value = 0
        
        # Itera sobre todos os itens no estoque
        stock_items = Stock.objects.all()
        for stock_item in stock_items:
            total_value += stock_item.acquisition_value


        return Response({
            "total_stock_value": (total_value)
        }, status=status.HTTP_200_OK)



class TotalSalesValueView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            total_sales_value = 0

            # Itera por todas as vendas e calcula o valor total
            sales = Sale.objects.all()
            for sale in sales:
                total_sales_value += sale.sale_quantity * sale.product.price
                

            return Response({"total_sales_value": total_sales_value}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)









from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from django.shortcuts import get_object_or_404



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




















class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Supondo que a requisição contém os dados necessários para a venda
        employee_id = request.data.get("employee")
        product_id = request.data.get("product")
        sale_quantity = request.data.get("sale_quantity")

        # Aqui você deve adicionar a lógica para criar a venda
        try:
            # Criar a venda
            sale = Sale.objects.create(
                employee_id=employee_id,
                product_id=product_id,
                sale_quantity=sale_quantity,
                # Adicione outros campos necessários
            )

            # Após criar a venda, esvaziar o carrinho
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



    
# views.py
# sales by employ with id
from rest_framework.exceptions import NotFound

class SalesByEmployeeWithIdViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

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
                'date'  # Data da venda (supondo que há um campo 'created_at' em Sale)
            )
        )

        # Retorna as vendas como uma resposta
        return Response({"employee_id": id, "sales": list(sales)}, status=status.HTTP_200_OK)



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

class ActionHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = ActionHistorySerializer
    #permission_classes = [IsAuthenticated]

    def get_queryset(self):
        employee_id = self.kwargs.get('employee_id')
        return ActionHistory.objects.filter(employee_id=employee_id) if employee_id else ActionHistory.objects.all()



# Token Authentication
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        user = authenticate(username=request.data['username'], password=request.data['password'])
        
        if user:
            try:
                employee = Employee.objects.get(user=user)
                
                response.data['employee'] = {
                    'id': employee.id,
                    'role': employee.role
                }
               
            except Employee.DoesNotExist:
                response.data['employee'] = None
                response.data['error'] = "Dados do funcionário não encontrados."
        else:
            response.data['error'] = "Credenciais inválidas."
            response.status_code = status.HTTP_401_UNAUTHORIZED

        return response


# ViewSets
class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    #permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        querysert = self.get_queryset()
        serializer = self.get_serializer(querysert, many=True)
        
        filtered_employees = [
            {
                'id': employee['id'],
                'name': employee['name'],
                'email': employee['email'],
                'contact': employee['contact'],
                'address': employee['address'],
                'role': employee['role']

            }

            for employee in serializer.data if employee['role'] == 'employee' 
        ]
        return Response(filtered_employees)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        data = request.data
        instance.name = data.get('name', instance.name)
        instance.role = data.get('role', instance.role)
        
        user = instance.user
        user.email = data.get('email', user.email)


        #  # Caso haja uma solicitação para atualizar a senha, faça o hash da nova senha
        # password = data.get("password", None)
        # if password:
        #     user.password = make_password(password)  # Hash da nova senha

        user.save()
      


        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        user = instance.user

        instance.delete()
        user.delete()

        return Response({
            'message': 'Employee and related user deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)






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




















# Employee Dashboard
class EmployeeDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            employee = Employee.objects.get(id=id)
            serializer = EmployeeSerializer(employee)
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response({"error": "Funcionário não encontrado"}, status=status.HTTP_404_NOT_FOUND)






class StockEntryView(APIView):
    authentication_classes  = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


    def post(self, request):
        product_id = request.data.get("product_id")

        quantity = request.data.get("quantity")

        reponsible_user = request.user.employee
       



        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({
                'error': 'Produto nao encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        stock_entry = Stock.objects.create(
            product = product,
            quantity=quantity,
            responsible_user = reponsible_user
        )


        return Response({
            'message': 'Produto Adicionado ao estoque com sucesso.',
            'product': {
                'id': stock_entry.product.id,
                'name': stock_entry.product.name,
                'quantity': stock_entry.quantity,
                'price': stock_entry.price
            }
        }, status=status.HTTP_201_CREATED)


from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db.models import Sum, F


class SalesByEmployee(viewsets.ViewSet):
    """
    ViewSet para retornar o total de vendas por funcionário.
    """

    def list(self, request):
        # Obtém todos os funcionários
        employees = Employee.objects.all()

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
