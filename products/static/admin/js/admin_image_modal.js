/* products/static/admin/js/admin_image_modal.js - 最终版本 */

// 我们不再依赖 IIFE 的参数映射，而是直接使用 django.jQuery
// 使用 setTimeout 确保我们的代码在 Admin 的其余 JS 之后运行
setTimeout(function() {
    // 再次检查，确保 django.jQuery 确实存在
    if (typeof django === 'undefined' || typeof django.jQuery === 'undefined') {
        console.error("致命错误：无法找到 django.jQuery。图片放大功能失效。");
        return;
    }

    const $ = django.jQuery; // 在这里定义一个局部变量 $ 方便后续代码书写

    $(document).ready(function() {
        // 1. 在页面底部注入模态框 HTML 结构
        $('body').append(`
            <div id="productImageModal" class="image-modal">
                <span class="image-modal-close">&times;</span>
                <img class="image-modal-content" id="imgModalContent">
            </div>
        `);

        var modal = $('#productImageModal');
        var modalImg = $('#imgModalContent');
        var closeModal = $('.image-modal-close');

        // 2. 捕获图片点击事件
        // 使用 #content-main 作为父元素监听事件，阻止事件冒泡干扰 Admin 内部逻辑
        $('#content-main').on('click', '.image-clickable', function(e) {
            e.preventDefault();
            e.stopPropagation();

            var clickedImg = $(this);
            var largeSrc = clickedImg.data('large-url');

            if (largeSrc) {
                modal.css('display', 'block');
                modalImg.attr('src', largeSrc);
                modal.focus();
            }
        });

        // 3. 监听关闭事件
        closeModal.on('click', function() {
            modal.css('display', 'none');
        });

        // 点击模态框背景关闭
        modal.on('click', function(e) {
            if ($(e.target).hasClass('image-modal')) {
                modal.css('display', 'none');
            }
        });

        // 键盘 Esc 键关闭
        $(document).on('keydown', function(e) {
            if (e.key === "Escape" && modal.css('display') === 'block') {
                modal.css('display', 'none');
            }
        });
    });
}, 0); // 使用 setTimeout 确保代码在浏览器 Event Loop 的下一个 tick 执行