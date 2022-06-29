from unicodedata import category
from django.shortcuts import render
from django.http import HttpResponse

from eshop.models import Product, Contact, Order, OrderUpdate
from .models import Product, Contact
from math import ceil
import json
from django.views.decorators.csrf import csrf_exempt
from .PayTm import Checksum
MERCHANT_KEY = 'gwQYyBAMS%NybMzl'

def index(request):
    # products =Product.objects.all()
    # print(products)
    # n = len(products)
    # print(n)
    # prod1 = products.first()
    # print(prod1.product_name)
    # nSlides = ceil(n/4)

    allProds = []
    catprods = Product.objects.values(  'category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])

    # params = {'no_of_slides':nSlides, 'range': range(1,nSlides),'product': products}
    # allProds = [[products, range(1, nSlides), nSlides],
    #             [products, range(1, nSlides), nSlides]]
    params = {'allProds':allProds}
    return render(request, 'eshop/index.html', params)


def searchMatch(query, item):
    '''return true only if query matches the item'''
    if query in item.product_desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False


def search(request):
    query= request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod=[item for item in prodtemp if searchMatch(query, item)]
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod)!= 0:
            allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds': allProds, "msg":""}
    if len(allProds)==0 or len(query)<3:
        params={'msg':"Please make sure to enter relevant search query"}
    return render(request, 'eshop/search.html', params)


def about(request):
    return render(request, 'eshop/about.html')


def contact(request):
    thank=False
    if request.method=="POST":
        print(request)
        name=request.POST.get('name', '')
        email=request.POST.get('email', '')
        phone=request.POST.get('phone', '')
        desc=request.POST.get('desc', '')
        print(name,email,phone, desc )
        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        thank=True
    return render(request, 'eshop/contact.html', {'thank':thank})


def tracker(request):
    if request.method=="POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try:
            order = Order.objects.filter(order_id=orderId, email=email)
            if len(order)>0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                response = json.dumps([updates, order[0].items_json], default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{}')
        except Exception as e:
            return HttpResponse('{}')
    return render(request, 'eshop/tracker.html')


def productView(request, myid):
    #Fetch the product using the id
    product=Product.objects.filter(id=myid)
    print(product)
    return render(request, 'eshop/prodView.html', {'product': product[0]})


def checkout(request):
    if request.method=="POST":
        items_json= request.POST.get('itemsJson', '')
        name=request.POST.get('name', '')
        amount = request.POST.get('amount', '')
        email=request.POST.get('email', '')
        address=request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city=request.POST.get('city', '')
        state=request.POST.get('state', '')
        zip_code=request.POST.get('zip_code', '')
        phone=request.POST.get('phone', '')
        print(amount)
        if amount!=0 :
            order = Order(items_json= items_json, name=name, email=email, address= address, city=city, state=state, zip_code=zip_code, phone=phone, amount=amount)
            order.save()
            update= OrderUpdate(order_id= order.order_id, update_desc="The order has been placed")
            update.save()
            thank=True
            id=order.order_id
            # return render(request, 'eshop/checkout.html', {'thank':thank, 'id':id})
            #request paytm to transfer the amount to your account after payment by user
            param_dict={

                    'MID': 'HHEBwK90416502889795',
                    'ORDER_ID': str(order.order_id),
                    'TXN_AMOUNT': str(amount),
                    'CUST_ID': email,
                    'INDUSTRY_TYPE_ID': 'Retail',
                    'WEBSITE': 'WEBSTAGING',
                    'CHANNEL_ID': 'WEB',
                    'CALLBACK_URL':'http://127.0.0.1:8000/eshop/handlerequest/',

            }
            param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, MERCHANT_KEY)
            return render(request, 'eshop/paytm.html', {'param_dict': param_dict})
    return render(request, 'eshop/checkout.html')


@csrf_exempt
def handlerequest(request):
    # paytm will send you the post here
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum = form[i]

    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            print('order successful')
        else:
            print('order was not successful because' + response_dict['RESPMSG'])
    return render(request, 'eshop/paymentstatus.html', {'response': response_dict})