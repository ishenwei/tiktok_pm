/* products/static/admin/js/product_tags.js */

// 🌟 修改：不再传入 django.jQuery，而是直接使用全局 jQuery ($)
// 因为我们在 admin.py 里引入了 code.jquery.com/jquery-3.6.0.min.js
(function($) {
    $(document).ready(function() {
        var $select = $('.tag-select2');

        if ($select.length > 0) {
            var colorMap = $select.data('colors');
            if (typeof colorMap === 'string') {
                try {
                    colorMap = JSON.parse(colorMap);
                } catch(e) {
                    colorMap = {};
                }
            }

            function formatTag(state) {
                if (!state.id) {
                    return state.text;
                }
                var color = colorMap[state.id] || '#ccc';
                var $state = $(
                    '<span><span class="tag-dot" style="background-color:' + color + ';"></span> ' + state.text + '</span>'
                );
                return $state;
            }

            // 现在这里的 .select2() 方法应该能找到了
            $select.select2({
                placeholder: "Select tags",
                allowClear: true,
                width: '100%',
                templateResult: formatTag,
                templateSelection: formatTag
            });
        }
    });
})(jQuery); // <--- 注意这里改成了 jQuery (全局对象)