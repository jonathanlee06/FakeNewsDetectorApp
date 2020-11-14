$('.navbar-nav .nav-item').click(function(){
    $('.navbar-nav .nav-link').removeClass('active');
    $(this).addClass('active');
})