$('.navbar-nav .nav-item').click(function(){
    $('.navbar-nav .nav-link').removeClass('active');
    $(this).addClass('active');
})

$(".alert").delay(4000).slideUp(200, function() {
    $(this).alert('close');
});