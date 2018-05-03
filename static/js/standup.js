$(function() {
    // Make the logout link submit the form with a CSRF token
    $('#logout-link').click(function(ev) {
        $('#logout-form').submit();
        return false;
    });

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
        if (minutes < 10) { // single digit
            minutes = '0' + minutes;
        }
        $t.text(hours + ':' + minutes + ' ' + ampm);
    });
}

function random(upper, lower) {
    if (!lower) {
        lower = 0;
    }
    return Math.floor(Math.random() * (upper - lower) + 1) + lower;
}
