import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.decorators import login_required
from django.db.models import Q , Sum,F
from .models import SellerLocation, SocialInfo, ProductInfo, BusinessProfile, Statistic
from accounts.models import CustomUser
from .utils import vincenty_distance, get_profile_completion
from django.shortcuts import render, redirect, get_object_or_404, redirect
from django.contrib import messages
from .forms import ProductForm, SocialInfoForm, SellerLocationForm
from django.core.paginator import Paginator
from django.urls import reverse
from datetime import timedelta, date


def index(request):
    return render (request, 'main/index.html')


import math
from collections import Counter, defaultdict

from django.db.models import Q, F, Value, FloatField, ExpressionWrapper, Exists, OuterRef, Prefetch
from django.db.models.functions import Power
from django.shortcuts import render
from django.utils import timezone


PAGE_SIZE = 5
SELLER_BATCH_SIZE = 25
DEFAULT_RADIUS_KM = 50
MAX_RADIUS_KM = 100


def get_bounding_box(latitude, longitude, radius_km):
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * max(math.cos(math.radians(latitude)), 0.01))

    return {
        "min_lat": latitude - lat_delta,
        "max_lat": latitude + lat_delta,
        "min_lon": longitude - lon_delta,
        "max_lon": longitude + lon_delta,
    }


def filter_sellers(request):
    platform = request.GET.get("platform")
    location = request.GET.get("location", "").strip()
    query = request.GET.get("query", "").strip()

    try:
        user_latitude = float(request.GET.get("latitude"))
        user_longitude = float(request.GET.get("longitude"))
    except (TypeError, ValueError):
        return render(request, "main/for_buyer.html", {
            "sellers": [],
            "query": query,
            "error": "Invalid location data.",
        })

    try:
        radius_km = float(request.GET.get("radius", DEFAULT_RADIUS_KM))
    except ValueError:
        radius_km = DEFAULT_RADIUS_KM

    radius_km = min(max(radius_km, 1), MAX_RADIUS_KM)

    try:
        page_number = max(int(request.GET.get("page", 1)), 1)
    except ValueError:
        page_number = 1

    terms = set()
    if query:
        terms = {query, f"{query}s", query.rstrip("s")}
        terms.discard("")

    product_filter = Q()
    social_product_filter = Q()

    for term in terms:
        product_filter |= (
            Q(product_name__icontains=term) |
            Q(product_descriptions__icontains=term)
        )
        social_product_filter |= (
            Q(product_infos__product_name__icontains=term) |
            Q(product_infos__product_descriptions__icontains=term)
        )

    product_qs = ProductInfo.objects.select_related("business_profile").only(
        "id",
        "product_name",
        "product_descriptions",
        "business_profile",
        "business_profile__product_category",
    )

    if terms:
        product_qs = product_qs.filter(product_filter)

    social_qs = SocialInfo.objects.only(
        "id",
        "user_id",
        "handle",
        "social_category",
    )

    matching_socials = SocialInfo.objects.filter(user_id=OuterRef("user_id"))

    if platform and platform != "all":
        social_qs = social_qs.filter(social_category__iexact=platform)
        matching_socials = matching_socials.filter(social_category__iexact=platform)

    if terms:
        social_qs = social_qs.filter(social_product_filter).distinct()
        matching_socials = matching_socials.filter(social_product_filter)
    else:
        social_qs = social_qs.filter(product_infos__isnull=False).distinct()
        matching_socials = matching_socials.filter(product_infos__isnull=False)

    social_qs = social_qs.prefetch_related(
        Prefetch("product_infos", queryset=product_qs, to_attr="matched_products")
    )

    bbox = get_bounding_box(user_latitude, user_longitude, radius_km)

    seller_qs = SellerLocation.objects.only(
        "id",
        "user_id",
        "latitude",
        "longitude",
        "location",
    )

    if location:
        seller_qs = seller_qs.filter(location__icontains=location)

    distance_score = ExpressionWrapper(
        Power(F("latitude") - Value(user_latitude), Value(2.0)) +
        Power((F("longitude") - Value(user_longitude)) * Value(math.cos(math.radians(user_latitude))), Value(2.0)),
        output_field=FloatField(),
    )

    seller_qs = seller_qs.annotate(
        has_matching_social=Exists(matching_socials),
        distance_score=distance_score,
    ).filter(
        has_matching_social=True,
    ).order_by("distance_score", "id").filter(
    latitude__gte=bbox["min_lat"],
    latitude__lte=bbox["max_lat"],
    longitude__gte=bbox["min_lon"],
    longitude__lte=bbox["max_lon"],
)


    needed_results = page_number * PAGE_SIZE + PAGE_SIZE
    flattened_sellers = []
    offset = 0

    while len(flattened_sellers) < needed_results:
        seller_batch = list(seller_qs[offset:offset + SELLER_BATCH_SIZE])

        if not seller_batch:
            break

        user_ids = [seller.user_id for seller in seller_batch]
        socials_by_user = defaultdict(list)

        for social in social_qs.filter(user_id__in=user_ids):
            socials_by_user[social.user_id].append(social)

        for seller in seller_batch:
            try:
                seller_latitude = float(seller.latitude)
                seller_longitude = float(seller.longitude)
            except ValueError:
                continue

            distance = vincenty_distance(
                user_latitude,
                user_longitude,
                seller_latitude,
                seller_longitude,
            )

            for social in socials_by_user.get(seller.user_id, []):
                for product in social.matched_products:
                    flattened_sellers.append({
                        "user_id": seller.user_id,
                        "distance": round(distance, 2),
                        "location": seller.location,
                        "product_info": product,
                        "social": social,
                    })

        offset += SELLER_BATCH_SIZE

    flattened_sellers.sort(key=lambda item: item["distance"])

    start = (page_number - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_items = flattened_sellers[start:end]

    appearance_counts = Counter(item["user_id"] for item in page_items)
    today = timezone.localdate()

    for user_id, count in appearance_counts.items():
        stat, _ = Statistic.objects.get_or_create(
            user_id=user_id,
            date_time=today,
            defaults={"appearence_count": 0},
        )
        Statistic.objects.filter(id=stat.id).update(
            appearence_count=F("appearence_count") + count
        )

    page_querystring = request.GET.copy()
    page_querystring.pop("page", None)
    page_querystring = page_querystring.urlencode()

    if page_querystring:
        page_querystring += "&"

    return render(request, "main/for_buyer.html", {
        "sellers": page_items,
        "query": query,
        "page_number": page_number,
        "previous_page_number": page_number - 1,
        "next_page_number": page_number + 1,
        "has_previous": page_number > 1,
        "has_next": len(flattened_sellers) > end,
        "page_querystring": page_querystring,
    })


def for_seller(request):
    return render (request, 'main/for_seller.html')

def seller_panel(request):
    handle=''
    user = request.user
    products = ProductInfo.objects.filter(user=user)
    handle = SocialInfo.objects.filter(user=user)
    today = date.today()
    last_week = today - timedelta(days=7)

    # This week
    current_stats = Statistic.objects.filter(user=user, date_time__gte=last_week, date_time__lte=today)
    current_appear = current_stats.aggregate(Sum('appearence_count'))['appearence_count__sum'] or 0
    current_copied = current_stats.aggregate(Sum('link_copied_count'))['link_copied_count__sum'] or 0

    # Previous week
    prev_start = last_week - timedelta(days=7)
    previous_stats = Statistic.objects.filter(user=user, date_time__gte=prev_start, date_time__lt=last_week)
    previous_appear = previous_stats.aggregate(Sum('appearence_count'))['appearence_count__sum'] or 0
    previous_copied = previous_stats.aggregate(Sum('link_copied_count'))['link_copied_count__sum'] or 0

    # Differences
    diff_appear = current_appear - previous_appear
    diff_copied = current_copied - previous_copied

    completion = get_profile_completion(request.user)

    location = user.sellerlocation.first()

    context = {
        'completion':completion,
        'current_appear': current_appear,
        'current_copied': current_copied,
        'diff_appear': diff_appear,
        'diff_copied': diff_copied,
        'products':products,
        'social':handle,
        'location':location,

    }
    return render(request, 'main/seller_panel.html', context)


def faqs_views(request):
    return render(request, 'main/faqs.html')



def edit_profile(request):
    if request.method == "POST":
        user = request.user

        # Get form values
        full_name = request.POST.get("full_name")
        location = request.POST.get("location")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        instagram = request.POST.get("instagram")
        facebook = request.POST.get("facebook")
        tiktok = request.POST.get("tiktok")
        business_name = request.POST.get('business_name')
        business_descriptions = request.POST.get('business_descriptions')
        product_category = request.POST.get('product_category')

        # Update full name
        if full_name:
            CustomUser.objects.update_or_create(
                email=user.email,
                defaults={'full_name': full_name}
            )

        # Update or create seller location
        if location:
            SellerLocation.objects.update_or_create(
                user=user,
                defaults={
                    'location': location,
                    'latitude': latitude,
                    'longitude': longitude
                }
            )

        # Update or create BusinessProfile
        business_profile, _ = BusinessProfile.objects.update_or_create(
            user=user,
            defaults={
                'business_name': business_name if business_name else '',
                'business_descriptions': business_descriptions if business_descriptions else '',
                'product_category': product_category if product_category else 'Other'
            }
        )

        # Get all user's products
        user_products = ProductInfo.objects.filter(user=user)

        # If no products exist, create a default one
        if not user_products.exists():
            default_product = ProductInfo.objects.create(
                user=user,
                business_profile=business_profile,
                product_name="Default Product",
                product_descriptions="Auto-created product for social links"
            )
            user_products = [default_product]

        # Save or update social handles
        socials = {
            'Facebook': facebook,
            'Instagram': instagram,
            'Tiktok': tiktok,
        }

        for category, handle in socials.items():
            if handle:
                if not handle.startswith('@'):
                    handle = '@'+handle

                # Update or create social handle
                social_obj, _ = SocialInfo.objects.update_or_create(
                    user=user,
                    social_category=category,
                    defaults={'handle': handle}
                )

                # Associate with all user's products
                social_obj.product_infos.set(user_products)

        profile_message = messages.success(request, "Profile updated successfully!")
        return redirect("main:edit-profile")

    return render(request, "main/seller_panel.html")


def add_product(request):
    if request.method == 'POST':
        product_name = request.POST.get('name')
        product_descriptions = request.POST.get('description')

        user = request.user

        # Get the business profile of the current user
        business_profile = BusinessProfile.objects.filter(user=user).first()

        if business_profile:
            # Creating the product
            product = ProductInfo.objects.create(
                user=user,
                product_name=product_name,
                product_descriptions=product_descriptions,
                business_profile=business_profile
            )

            # Get all social handles of the user
            social_handles = SocialInfo.objects.filter(user=user)

            # Associate the product with each social handle (ManyToMany)
            for social in social_handles:
                social.product_infos.add(product)

            messages.success(request, "Product added and associated with your social handles successfully!")
        else:
            messages.error(request, "You must first create a business profile before adding products.")

        # Redirect back to seller panel
        url = reverse('main:seller-panel')
        return redirect(f'{url}#products')

    return render(request, 'main/seller_panel.html')

def edit_product_info(request, pk):
    product = get_object_or_404(ProductInfo, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product details updated successfully.')
            return redirect('main:edit-product', product.pk)
    else:
        form = ProductForm(instance=product)

    return render(request, 'main/edit_product_info.html', {'form': form, 'product': product})


def delete_product(request, pk):
    product = get_object_or_404(ProductInfo, pk=pk, user=request.user)

    if request.method == 'POST':
        product_name = product.product_name 
        product.delete()
        messages.success(request, f'{product_name} was deleted successfully!')
        url = reverse('main:seller-panel')
        return redirect(f'{url}#products')

    return render(request, 'main/confirm_delete.html', {'product': product})


@csrf_exempt  
def update_statistics(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        handle_id = data.get('handle_id')

        try:
            user = CustomUser.objects.get(id=handle_id)
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        # Check if Statistic exists; if not, create it
        today = date.today()
        statistic, created = Statistic.objects.get_or_create(user=user, date_time=today)
        statistic.link_copied_count += 1
        statistic.save()

        return JsonResponse({
            'success': 'Link copy count updated',
            'new_count': statistic.link_copied_count,
            'created': created
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
