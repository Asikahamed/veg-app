from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, CartItem, Order, OrderItem
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseRedirect

def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'product_detail.html', {'product': product})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    return redirect('cart')

@login_required(login_url='/login/')
def cart(request):
    items = CartItem.objects.filter(user=request.user)
    return render(request, 'cart.html', {'cart_items': items})

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items.exists():
        return redirect('cart')

    total = sum(item.quantity * item.product.discounted_price for item in cart_items)

    if request.method == "POST":
        address = request.POST.get('address', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()

        if not address or not contact_number:
            return render(request, 'checkout.html', {
                'cart_items': cart_items,
                'cart_total': total,
                'error': 'Both address and contact number are required.'
            })

        # Create a single Order
        order = Order.objects.create(
            user=request.user,
            address=address,
            contact_number=contact_number,
            total_price=total,
        )

        # Create OrderItem entries for each cart item
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.discounted_price
            )

        cart_items.delete()
        return render(request, 'checkout_success.html', {'total': total})

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'cart_total': total,
    })
