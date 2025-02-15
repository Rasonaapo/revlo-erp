from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from operations.models.operations import Inventory, ProductCategory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, render

class InventoryListView(LoginRequiredMixin, ListView):
    model = Inventory
    template_name = 'operations/inventory/inventory_list.html'
    context_object_name = 'inventory'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = 'Inventory List'
        return context

class ProductCategoryListView(LoginRequiredMixin, ListView):
    # generate a similar view just like the others in other apps
    model = ProductCategory
    template_name = 'operations/inventory/product_category_list.html'
    context_object_name = 'product_category'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = 'Product Category List'
        return context

class ProductCategoryCreateView(LoginRequiredMixin, CreateView):
    model = ProductCategory
    template_name = 'operations/inventory/product_category_form.html'
    fields = ['category_name', 'description']
    success_url = reverse_lazy('product-category-list')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = 'Add Product Category'
        return context
    
class ProductCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductCategory
    template_name = 'operations/inventory/product_category_form.html'
    fields = ['category_name', 'description']
    success_url = reverse_lazy('product-category-list')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = f'Update {self.object.category_name}'
        return context

class ProductCategoryDetailView(LoginRequiredMixin, DetailView):
    model = ProductCategory
    template_name = 'operations/inventory/product_category_detail.html'
    context_object_name = 'product_category'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = f'Detail {self.object.category_name}'
        return context

def delete_product_category(request, pk):
    try:
        product_category = ProductCategory.objects.get(pk=pk)
    except ProductCategory.DoesNotExist:
        raise Http404("Product Category does not exist")
    
    if request.method == "POST":
        product_category.delete()
        messages.success(request, f"{product_category.category_name} has been deleted")
        return redirect('product-category-list')

    return render(request, 'core/delete.html', {'obj':product_category, 'title': f'Delete {product_category}?'})
