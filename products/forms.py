# products/forms.py

from django import forms
from .models import Product, ProductTagDefinition
import json


class ProductAdminForm(forms.ModelForm):
    # 定义一个伪字段用于前端交互
    tags_selector = forms.MultipleChoiceField(
        required=False,
        label="Tags",
        widget=forms.SelectMultiple(attrs={'class': 'tag-select2'})
    )

    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. 获取所有定义的 Tag
        tags = ProductTagDefinition.objects.all()
        choices = [(t.code, t.name) for t in tags]

        # 2. 构建颜色映射表 (用于 JS 显示颜色)
        color_map = {t.code: t.color for t in tags}

        # 3. 配置 tags_selector 字段
        self.fields['tags_selector'].choices = choices

        # 🌟 关键：把颜色数据注入到 data-colors 属性中，供 JS 读取
        self.fields['tags_selector'].widget.attrs.update({
            'data-colors': json.dumps(color_map)
        })

        # 4. 如果是编辑现有产品，初始化选中的 Tags
        if self.instance and self.instance.pk and self.instance.tags:
            # self.instance.tags 是一个 JSON List (['new', 'hot'])
            # Select2 需要这个列表来自动选中对应项
            self.initial['tags_selector'] = self.instance.tags

    def save(self, commit=True):
        # 5. 保存时，把 Select2 选中的数据 (List) 存回 instance.tags (JSONField)
        instance = super().save(commit=False)
        instance.tags = self.cleaned_data.get('tags_selector', [])
        if commit:
            instance.save()
        return instance