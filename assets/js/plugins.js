// place any jQuery/helper plugins in here, instead of separate, slower script files.
function entryradio() {
    var row, el;
    $("input[type=radio]").click(function() {
	el = $(this);
	row = el.data("row");
	$("input[data-row=" + row + "]").prop("checked", false);
	el.prop("checked", true);
    });
}
