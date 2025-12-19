/* products/static/admin/js/admin_image_modal.js */

// 🌟 修改：传入全局 jQuery 以保持一致性
(function($) {
    $(document).ready(function() {
        // ... (原有的模态框 HTML 注入代码保持不变) ...
        if ($('#admin-media-modal').length === 0) {
            $('body').append(`
                <div id="admin-media-modal" class="admin-media-modal">
                    <span class="admin-media-close">&times;</span>
                    <img class="admin-media-content" id="media-modal-img" style="display:none;">
                    <video class="admin-media-content" id="media-modal-video" controls style="display:none;">
                        Your browser does not support the video tag.
                    </video>
                    <div id="admin-media-caption"></div>
                </div>
            `);
        }

        var $modal = $('#admin-media-modal');
        var $modalImg = $('#media-modal-img');
        var $modalVideo = $('#media-modal-video');
        var $caption = $('#admin-media-caption');
        var videoElement = $modalVideo[0];

        // ... (图片点击逻辑保持不变) ...
        $(document).on('click', '.image-clickable', function() {
             var src = $(this).data('large-url') || $(this).attr('src');
             $modal.show();
             $modalVideo.hide();
             if(videoElement) videoElement.pause();
             $modalImg.attr('src', src).show();
             $caption.text("Image Preview");
        });

        // ... (视频点击逻辑保持不变) ...
        $(document).on('click', '.video-clickable-wrapper', function() {
            var videoUrl = $(this).data('video-url');
            if (videoUrl) {
                $modal.show();
                $modalImg.hide();
                $modalVideo.attr('src', videoUrl).show();
                $caption.text("Video Preview");
                if(videoElement) {
                    videoElement.play().catch(function(e) { console.log("Autoplay prevented"); });
                }
            }
        });

        // ... (关闭逻辑保持不变) ...
        function closeModal() {
            $modal.hide();
            if(videoElement) videoElement.pause();
            $modalVideo.attr('src', '');
            $modalImg.attr('src', '');
        }

        $('.admin-media-close').on('click', closeModal);
        $modal.on('click', function(e) {
            if (e.target === this) closeModal();
        });
        $(document).on('keydown', function(e) {
            if (e.key === "Escape") closeModal();
        });
    });
})(jQuery); // <--- 注意这里改成了 jQuery