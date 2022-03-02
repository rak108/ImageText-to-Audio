$("form").on('submit',function (e) {
    e.stopPropagation();
    e.preventDefault();

    // TODO: Add form validation
    $.ajax({
        type: 'post',
        url: '/upload-image',
        data: $('form').serialize(), // TODO: Send a File
        success: function (q) {
            document.getElementById("result").innerHTML= q;
        }
    });
});