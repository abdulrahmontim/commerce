from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from decimal import Decimal, InvalidOperation

from .models import User, Listing, Category, Bid, Comment


def index(request):

    return render(request, "auctions/index.html", {
        "listings": Listing.objects.all(),
        "watchlist": request.user.watchlist.all() if request.user.is_authenticated else []        
    })


def listing(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    comments = listing.comments.all()
    watchlist = request.user.watchlist.all() if request.user.is_authenticated else []
    bids = listing.bids.all()
    highest_bid = bids.order_by("-amount").first()
    
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "comments": comments,
        "watchlist": watchlist,
        "starting_bid": listing.starting_bid,
        "highest_bid": highest_bid,
        "bids": bids
        })

@login_required
def categories(request):
    return render(request, "auctions/categories.html", {
        "categories": Category.objects.all()
    })
    
@login_required
def category(request, category_id):
    category = Category.objects.get(pk=category_id)
    listing = Listing.objects.filter(category=category, active=True)
    watchlist = request.user.watchlist.all() if request.user.is_authenticated else []
    
    return render(request, "auctions/category.html", {
        "category": category,
        "listings": listing,
        "watchlist": watchlist
    })

@login_required
def watchlist(request):
    watchlist = request.user.watchlist.all() if request.user.is_authenticated else []
    
    return render(request, "auctions/watchlist.html", {
        "listings": watchlist,
        "watchlist": watchlist
    })
    
@login_required
def toggle_watchlist(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    
    if listing in request.user.watchlist.all():
        request.user.watchlist.remove(listing)
        messages.info(request, f"{listing.title} removed from watchlist.")
    else:
        request.user.watchlist.add(listing)
        messages.success(request, f"{listing.title} added to watchlist!")
    
    # return  HttpResponseRedirect(reverse("listing", args=[listing_id]))  
    previous_page = request.META.get('HTTP_REFERER')
    if previous_page:
        return HttpResponseRedirect(previous_page)
    else:
        return HttpResponseRedirect("listing", args=[listing_id])
        
@login_required
def create_listing(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        starting_bid = request.POST.get("starting_bid")
        image_url = request.POST.get("image_url")
        category_id = request.POST.get("category")
        category = Category.objects.get(pk=category_id) if category_id else None
        
        new_listing = Listing(
            title=title,
            description=description,
            starting_bid=starting_bid,
            image=image_url,
            category=category,
            creator=request.user,
        )
        new_listing.save()

        messages.success(request, "Your listing was created successfully!")
        return HttpResponseRedirect(reverse("index"))

    categories = Category.objects.all()
    return render(request, "auctions/create_listing.html", {
        "categories": categories
    })
    
# @login_required
def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    listings = Listing.objects.filter(creator=user)
    won_listings = Listing.objects.filter(winner=user)
    
    return render(request, "auctions/profile.html", {
        "profile_user": user,
        "listings": listings,
        "won_listings": won_listings,
        
    })
    
@login_required
def edit_comment(request, comment_id):
    if request.method == "POST":
        comment = get_object_or_404(Comment, pk=comment_id)
        
        if request.user == comment.author:
            content = request.POST.get("content").strip()
            
            if content:
                comment.content = content
                comment.save()
                messages.success(request, "Your comment was updated successfully!")
            else:
                messages.error(request, "Comment cannot be empty.")
        
            return HttpResponseRedirect(reverse("listing", args=[comment.listing.id]))
        
    return HttpResponseRedirect(reverse("listing", args=[comment.listing.id]))
    
@login_required
def add_comment(request, listing_id):
    if request.user.is_authenticated:
        if request.method == "POST":
            listing = get_object_or_404(Listing, pk=listing_id)
            content = request.POST.get("content").strip()
            
            if content:
                comment = Comment.objects.create(
                    content=content,
                    author = request.user,
                    listing = listing
                )
                comment.save()
                messages.success(request, "Your comment was added successfully!")
            else:
                messages.error(request, "Comment cannot be empty.")
            
            return HttpResponseRedirect(reverse("listing", args=[listing_id]))
        return  HttpResponseRedirect(reverse("listing", args=[listing_id]))
            
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    
    if request.user == comment.author:
        comment.delete()
        messages.success(request, "Your comment was deleted successfully!")
        return HttpResponseRedirect(reverse("listing", args=[comment.listing.id]))
    else:
        messages.error(request, "You are not authorized to delete this comment.")
        return HttpResponseRedirect(reverse("listing", args=[comment.listing.id]))

@login_required
def close_listing(request, listing_id):
    if request.method == "POST":
        listing = get_object_or_404(Listing, pk=listing_id)
        
        if request.user == listing.creator:
            if listing.active:
                listing.active = False
                highest_bid = listing.bids.order_by("-amount").first()
                
                if highest_bid:
                    listing.winner = highest_bid.bidder
                    listing.save()
                    messages.success(request, f"{listing.title} has been closed. Winner: {listing.winner.username} with a bid of ${highest_bid.amount:.2f}.")
                    return HttpResponseRedirect(reverse("listing", args=[listing_id]))
                else:
                    listing.save()
                    messages.info(request, f"{listing.title} has been closed with no bids placed.")
                    return HttpResponseRedirect(reverse("listing", args=[listing_id]))
            else:
                messages.info(request, f"{listing.title} is already closed.")
                return HttpResponseRedirect(reverse("listing", args=[listing_id]))
        else:
            messages.error(request, "You are not authorized to close this listing.")
            return HttpResponseRedirect(reverse("listing", args=[listing_id]))
    
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))
        
        
    
@login_required
def place_bid(request, listing_id):
    if request.method == "POST":
        listing = get_object_or_404(Listing, pk=listing_id)
        
        if request.user == listing.creator:
            messages.error(request, "You cannot bid on your own listing.")
            return  HttpResponseRedirect(reverse("listing", args=[listing_id]))
        
        try:
            bid_amount = Decimal(request.POST.get("bid"))
        except (InvalidOperation, TypeError):
            messages.error(request, "Please enter a valid bid amount.")
            return  HttpResponseRedirect(reverse("listing", args=[listing_id]))
        
        if bid_amount <= 0:
            messages.error(request, "Bid must be greater than 0.")
            return  HttpResponseRedirect(reverse("listing", args=[listing_id]))
            
        if not listing.active:
            messages.error(request, "This listing is closed. You cannot place a bid.")
            return  HttpResponseRedirect(reverse("listing", args=[listing_id]))
        
        bids = listing.bids.all()
        starting_bid = Decimal(listing.starting_bid)
        
        if bids.exists():
            highest_bid = bids.order_by("-amount").first().amount
            if bid_amount <= highest_bid:
                messages.error(request, f"Your bid must be higher than ${highest_bid:.2f}.")
                return  HttpResponseRedirect(reverse("listing", args=[listing_id]))
        else:
            if bid_amount < starting_bid:
                messages.error(request, f"Your bid must be at least ${starting_bid:.2f}.")
                return  HttpResponseRedirect(reverse("listing", args=[listing_id]))
        
        Bid.objects.create(
            amount=bid_amount,
            bidder=request.user,
            listing=listing
        )
        
        messages.success(request, "Your bid was placed successfully!")
        return  HttpResponseRedirect(reverse("listing", args=[listing_id]))

    return  HttpResponseRedirect(reverse("listing", args=[listing_id]))

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            next_url = request.POST.get("next")
            return HttpResponseRedirect(next_url) if next_url else HttpResponseRedirect(reverse("index"))
        else:
            return render(
                request,
                "auctions/login.html",
                {"message": "Invalid username and/or password."},
            )
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        if not email:
            return render(request, "auctions/register.html", {"message": "Email cannot be blank."})
        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password and confirmation:
            if password != confirmation:
                return render(
                    request, "auctions/register.html", {"message": "Passwords must match."}
                )
        else:
            return render(request, "auctions/register.html", {"message": "Password cannot be blank."})
            

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(
                request,
                "auctions/register.html",
                {"message": "Username already taken."},
            )
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
