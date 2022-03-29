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

// $("#calculator_tags li").click(function() {
//   $(this).addClass('activeLI').siblings().removeClass('activeLI');
//   let valueEle = $(this).children().text();
//   $('#main_calculator_id').val(valueEle);
// })

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
});
// Change Header Text Dynamically
$('.list-group-item').on('click', function(e) {
  var el = $(this);
  sessionStorage.navItem = el.text();
});

$('.headerContainerLeft h3').text(sessionStorage.navItem);

let nvText = document.querySelector('.headerContainerLeft h3').innerText;

if(nvText == "Admin" || nvText == "admin") {
  $('.headerContainerLeft h3').text('');
  // sessionStorage.navItem = 'Calculator';
}

// Add active class on sidebar nav items

let createSec = $('#createSce');
let sceRepo = $('#createSceRepo');
let admin = $('#admin');

let createSecMob = $('#createSceMob');
let sceRepoMob = $('#createSceRepoMob');
let adminMob = $('#adminMob');

let subMenuParent = $('.submenuParent');
let subMenuParent2 = $('.submenuParent2')

$(document).ready(function() {
  $(".list-group-item").each(function(index) {
  if ($(this).attr('id') == sessionStorage.getItem("Activeli")) {
    $(this).addClass("sideActive");
    addShow();
  }
  });
  response = JSON.parse(sessionStorage.getItem("wishlistID"));
    $('a[data-pdtId="' + response + '"]').addClass('sideActive')
  });

  $('.list-group-item').click(function() {
    $(".list-group-item").removeClass("sideActive");
    $(this).addClass("sideActive");
    var id = $(this).attr("id");
    sessionStorage.setItem("Activeli", id);
  });

  function addShow() {
    if(createSec.hasClass('sideActive') || sceRepo.hasClass('sideActive') || createSecMob.hasClass('sideActive') || sceRepoMob.hasClass('sideActive')) {
      createSec.parent().addClass('show');
      sceRepo.parent().addClass('show');
      createSecMob.parent().addClass('show');
      sceRepoMob.parent().addClass('show');
      subMenuParent.attr('aria-expanded','true');
      admin.parent().removeClass('show');
      adminMob.parent().removeClass('show');
      subMenuParent2.attr('aria-expanded','false');
    }

    else if(admin.hasClass('sideActive') || adminMob.hasClass('sideActive')) {
      admin.parent().addClass('show');
      adminMob.parent().addClass('show');
      subMenuParent2.attr('aria-expanded','true');
      createSec.parent().removeClass('show');
      sceRepo.parent().removeClass('show');
      createSecMob.parent().removeClass('show');
      sceRepoMob.parent().removeClass('show');
      subMenuParent.attr('aria-expanded','false');
    }
  }