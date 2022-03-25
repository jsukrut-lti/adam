// Hide submenus
  $(document).ready(function () {

    // SidebarCollapse()
  });

//  $('#body-row .collapse').collapse('hide');

  // Collapse/Expand icon
  $('#collapse-icon').addClass('fa-angle-double-left');

  // Collapse click
  $('[data-toggle=sidebar-colapse]').click(function () {
    SidebarCollapse();
  });

  function SidebarCollapse() {
    $('.menu-collapsed').toggleClass('d-none');
    $('.sidebar-submenu').toggleClass('d-none');
    $('.submenu-icon').toggleClass('d-none');
    $('#sidebar-container').toggleClass('sidebar-expanded sidebar-collapsed');

    // Treating d-flex/d-none on separators with title
    var SeparatorTitle = $('.sidebar-separator-title');
    if (SeparatorTitle.hasClass('d-flex')) {
      SeparatorTitle.removeClass('d-flex');
    } else {
      SeparatorTitle.addClass('d-flex');
    }

    // Collapse/Expand icon
    $('#collapse-icon').toggleClass('fa-angle-double-left fa-angle-double-right');
  }

// SideBar Navigation
function openNav() {
  $('#sideNav').toggleClass('sideNavWidth');
  $('body').toggleClass('hidden');
}

$("#calculator_tags li").click(function() {
  $(this).addClass('activeLI').siblings().removeClass('activeLI');
  let valueEle = $(this).children().text();
  $('#main_calculator_id').val(valueEle);
})

// $('.django-plotly-dash.django-plotly-dash-iframe.django-plotly-dash-app-analysisapp.card').each(
//   function(){
//     if ($(this).has('_dash-loading-callback')){
//         $(this).addClass('dashLoader');
//     }
//     setTimeout(function() {
//         $('.django-plotly-dash.django-plotly-dash-iframe.django-plotly-dash-app-analysisapp.card').removeClass('dashLoader');
//     }, 3000);
// });