$(function() {
    fixTimezones();
});

/* Find all datetime objects and modify them to match the user's current
 * timezone. */
function fixTimezones() {
    $('time').each(function(elem) {
        var $t = $(this);

        var utc_dt_str = $t.attr('datetime');
        var local_dt = new Date(utc_dt_str);

        var hours = local_dt.getHours();
        var minutes = local_dt.getMinutes();
        var ampm = 'am';
        if (hours > 12) {
            hours -= 12;
            ampm = 'pm';
        }
        $t.text(hours + ':' + minutes + ' ' + ampm);
    });
}
