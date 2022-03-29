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
