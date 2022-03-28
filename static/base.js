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
    let calculator_id = $(this).children().attr("id");
    const url = "/get_calculator_version"
    $.ajax({
        type : 'GET',
        url: url,
        data: {
            'calculator_id': calculator_id
        },
        beforeSend: function(){
            return confirm("Warning !! \n Changing the Calculator version will unsave your changes. Are you sure you want to proceed?");
        },
        success: function (data) {
            var msg = 'Version changed';
            if (data.length > 0) {
                msg = 'Version changed to ' + data[0]
            }
            alert(msg);
            let valueEle = $(this).children().text();
            $(this).addClass('activeLI').siblings().removeClass('activeLI');
            $('#main_calculator_id').val(valueEle);
            location.reload();
        },
            error: function () {
            alert('Oops!!!!! Something went wrong. Please try back after later');
        },
    });

})