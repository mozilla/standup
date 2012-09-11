$(function() {
    fixTimezones();

    /* Authenticatication for Persona */
    $('#login').click(function(ev) {
        ev.preventDefault();
        navigator.id.request();
    });

    $('#logout').click(function(ev) {
        ev.preventDefault();
        navigator.id.logout();
    });

    navigator.id.watch({
        loggedInEmail: currentUser,
        onlogin: function(assertion) {
            $.ajax({
                type: 'POST',
                url: '/authenticate',
                data: { assertion: assertion },
                success: function(res, status, xhr) {
                    window.location.reload();
                },
                error: function(res, status, xhr) {
                    alert('login failure ' + res);
                }
            });
        },
        onlogout: function() {
            $.ajax({
                type: 'POST',
                url: '/logout',
                success: function(res, status, xhr) {
                    window.location.reload();
                },
                error: function(res, status, xhr) {
                    console.log('logout failure ' + res);
                }
            });
        }
    });
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
