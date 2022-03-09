$(document).ready( function () {
    $('#bauMax20').DataTable({
        "pageLength": 5,
        // ordering: false,
        paging: false,
        searching: false,
        info : false,
        order: [],
        'columnDefs': [{
            'targets': [0,1,3,5,7],
            'orderable': false,
        }],
        "language": {
            "lengthMenu": 'Display <select>'+
              '<option value="5">5</option>'+
              '<option value=5">10</option>'+
              '<option value="15">15</option>'+
              '<option value="20">20</option>'+
              '<option value="-1">All</option>'+
              '</select> Records'
          },
    });

    $('#bauMaxPerInc').DataTable({
        "pageLength": 5,
        ordering: false,
        paging: false,
        searching: false,
        info : false,
        "language": {
            "lengthMenu": 'Display <select>'+
              '<option value="5">5</option>'+
              '<option value="10">10</option>'+
              '<option value="15">15</option>'+
              '<option value="20">20</option>'+
              '<option value="-1">All</option>'+
              '</select> Records'
          },
    });

    $('#bauVolThreshold').DataTable({
        "pageLength": 5,
        ordering: false,
        paging: false,
        searching: false,
        info : false,
        "language": {
            "lengthMenu": 'Display <select>'+
              '<option value="5">5</option>'+
              '<option value="10">10</option>'+
              '<option value="15">15</option>'+
              '<option value="20">20</option>'+
              '<option value="-1">All</option>'+
              '</select> Records'
          },
    });

    $('#bauImpactThreshold').DataTable({
        "pageLength": 5,
        ordering: false,
        paging: false,
        searching: false,
        info : false,
        "language": {
            "lengthMenu": 'Display <select>'+
              '<option value="5">5</option>'+
              '<option value="10">10</option>'+
              '<option value="15">15</option>'+
              '<option value="20">20</option>'+
              '<option value="-1">All</option>'+
              '</select> Records'
          },
    });

    $('#combineAvg').DataTable({
        "pageLength": 5,
        ordering: false,
        paging: false,
        searching: true,
        info : false,
        "language": {
            "lengthMenu": 'Display <select>'+
              '<option value="5">5</option>'+
              '<option value="10">10</option>'+
              '<option value="15">15</option>'+
              '<option value="20">20</option>'+
              '<option value="-1">All</option>'+
              '</select> Records'
          },
          initComplete: function () {
            this.api().columns(0).every( function () {
                var column = this;
                var select = $('<select><option value="">Ownership</option></select>')
                    .appendTo( $(column.header()).empty() )
                    .on( 'change', function () {
                        var val = $.fn.dataTable.util.escapeRegex(
                            $(this).val()
                        );

                        column
                            .search( val ? '^'+val+'$' : '', true, false )
                            .draw();
                    } );

                column.data().unique().sort().each( function ( d, j ) {
                    select.append( '<option value="'+d+'">'+d+'</option>' )
                } );
            } );
        }
    });

// Project Code Starts Here

    $("#journal_code").change(function () {

        console.log('url ====');
        const url = $("#dataForm").attr("data-calc-url");
        const journalCode = $(this).val();
        const is_adj_inflation = $('#is_adj_inflation').is(':checked');

        $.ajax({
            url: url,
            data: {
                'journal_code': journalCode,
                'is_adj_inflation': is_adj_inflation
            },
            beforeSend: function(){
                $(".loader").show();
            },
            success: function (data) {
                var data_string = JSON.stringify(data);
                var parse_data = JSON.parse(data_string);
                var cur_chng_list = ['new_price_usd','new_price_eur','new_price_gbp','inf_new_price_usd','inf_new_price_eur','inf_new_price_gbp']
                var keyObj = {};
                for (let key in parse_data) {
                    if (cur_chng_list.includes(key)) {
                        keyObj[key] = parse_data[key];
                    }
                    $('#'+key).val(parse_data[key]);
                }
                $('#new_cur_price').val(JSON.stringify(keyObj));
                apply_price_change($('#new_price_usd').val(),$('#current_price').val());
            },
            error: function () {
                alert('Oops! Something went wrong. Please try back after later');
            },
            complete:function(data){
                $(".loader").hide();
            }
        });
    });

    $("#journal_acode").change(function () {
        const journal_acode_attr = $(this).attr("data-attr");
        const result = this.selectedIndex != 0 ? $(this).val() : '-';
        $('#'+journal_acode_attr).val(result);
    });

    $("#is_adj_inflation").change(function () {
          const is_adj_inflation = $(this).is(':checked');
          const data = $('#new_cur_price').val();
          if ((data.trim()).length != 0) {
              var parse_data = JSON.parse(data);
                for (let key in parse_data) {
                    let text = key.split("_");
                    if (is_adj_inflation === true) {
                        if (key.includes('inf_') === true) {
                            let text = key.split("_");
                            text.shift();
                            text = text.join("_");
                            $('#'+text).val(parse_data[key]);
                        }
                    }
                    else {
                        if (key.includes('inf_') != true) {
                            text = text.join("_");
                            $('#'+text).val(parse_data[key]);
                        }
                    }
                }
                apply_price_change($('#new_price_usd').val(),$('#current_price').val())
          }
    });

    $('#journal_code').select2({});
    $('#journal_acode').select2({});

    $("#dd_calculator").change(function () {
        const calculator_id = $(this).val();
        calculator_data_load(calculator_id);
    });

});

function apply_price_change(current_price,new_price) {
    let price_change = new_price - current_price;
    $('#price_change').val(price_change);
}

function calculator_data_load(calculator_id){

    $("#calculator_mod").html("");
    const url = "/get_calculator_data"
    $.ajax({
            url: url,
            data: {
                'calculator_id': calculator_id
            },
            beforeSend: function(){
                $(".loader").show();
            },
            success: function (data) {
                $("#calculator_mod").html(data);
            },
            error: function () {
                alert('Oops! Something went wrong. Please try back after later');
            },
            complete:function(data){
                $(".loader").hide();
            }
        });
}
// Project Code Starts Here
