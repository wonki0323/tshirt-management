from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Product, ProductOption
from .forms import ProductForm, ProductOptionFormSet


@login_required
def inventory_list(request):
    """재고 현황 조회"""
    # 모든 제품 옵션을 조회 (재고 추적 여부 무관)
    options = ProductOption.objects.filter(
        is_active=True
    ).select_related('product').order_by('product__name', 'option_detail')
    
    # 재고 부족 경고
    low_stock_count = 0
    out_of_stock_count = 0
    
    for option in options:
        if option.track_inventory and option.stock_quantity is not None:
            if option.stock_quantity <= 0:
                out_of_stock_count += 1
            elif option.stock_quantity <= 10:
                low_stock_count += 1
    
    context = {
        'options': options,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }
    
    return render(request, 'products/inventory_list.html', context)


class ProductListView(LoginRequiredMixin, ListView):
    """제품 목록 조회"""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    ordering = ['name']


class ProductCreateView(LoginRequiredMixin, CreateView):
    """제품 생성"""
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProductOptionFormSet(self.request.POST)
        else:
            context['formset'] = ProductOptionFormSet()
        return context
    
    def form_valid(self, form):
        import logging
        logger = logging.getLogger(__name__)
        
        context = self.get_context_data()
        formset = context['formset']
        
        logger.info(f"=== 제품 생성 시작 ===")
        logger.info(f"제품명: {form.cleaned_data.get('name')}")
        logger.info(f"Formset valid: {formset.is_valid()}")
        
        if not formset.is_valid():
            logger.error(f"Formset errors: {formset.errors}")
            logger.error(f"Formset non-form errors: {formset.non_form_errors()}")
            for i, form_errors in enumerate(formset.errors):
                if form_errors:
                    logger.error(f"Form {i} errors: {form_errors}")
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(self.request, f'제품 "{self.object.name}"이 성공적으로 생성되었습니다.')
            return super().form_valid(form)
        else:
            messages.error(self.request, '옵션 정보에 오류가 있습니다. 다시 확인해주세요.')
            return self.render_to_response(self.get_context_data(form=form))


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    """제품 수정"""
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProductOptionFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = ProductOptionFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        import logging
        logger = logging.getLogger(__name__)
        
        context = self.get_context_data()
        formset = context['formset']
        
        logger.info(f"=== 제품 수정 시작 ===")
        logger.info(f"제품명: {form.cleaned_data.get('name')}")
        logger.info(f"Formset valid: {formset.is_valid()}")
        
        if not formset.is_valid():
            logger.error(f"Formset errors: {formset.errors}")
            logger.error(f"Formset non-form errors: {formset.non_form_errors()}")
            for i, form_errors in enumerate(formset.errors):
                if form_errors:
                    logger.error(f"Form {i} errors: {form_errors}")
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(self.request, f'제품 "{self.object.name}"이 성공적으로 수정되었습니다.')
            return super().form_valid(form)
        else:
            messages.error(self.request, '옵션 정보에 오류가 있습니다. 다시 확인해주세요.')
            return self.render_to_response(self.get_context_data(form=form))


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    """제품 삭제"""
    model = Product
    template_name = 'products/product_confirm_delete.html'
    success_url = reverse_lazy('product_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            product = self.get_object()
            product_name = product.name
            
            # 관련 주문 항목이 있는지 확인
            from orders.models import OrderItem
            related_orders = OrderItem.objects.filter(product_option__product=product)
            
            if related_orders.exists():
                messages.error(request, f'제품 "{product_name}"은 {related_orders.count()}개의 주문에서 사용되고 있어 삭제할 수 없습니다.')
                return redirect('product_list')
            
            # 제품 삭제
            product.delete()
            messages.success(request, f'제품 "{product_name}"이 성공적으로 삭제되었습니다.')
            return redirect('product_list')
            
        except Exception as e:
            messages.error(request, f'제품 삭제 중 오류가 발생했습니다: {str(e)}')
            return redirect('product_list')