from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("listing/<int:listing_id>", views.listing, name="listing"),
    path("categories", views.categories, name="categories"),
    path("category/<int:category_id>", views.category, name="category"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("toggle_watchlist/<int:listing_id>", views.toggle_watchlist, name="toggle_watchlist"),
    path("create_listing", views.create_listing, name="create_listing"),
    path("user/<str:username>", views.user_profile, name="user_profile"),
    path("edit_comment/<int:comment_id>", views.edit_comment, name="edit_comment"),
    path("add_comment/<int:listing_id>", views.add_comment, name="add_comment"),
    path("delete_comment/<int:comment_id>", views.delete_comment, name="delete_comment"),
    path("close_listing/<int:listing_id>", views.close_listing, name="close_listing"),
    path("place_bid/<int:listing_id>", views.place_bid, name="place_bid"),
    
]
