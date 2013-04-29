function xsrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    crossDomain: false,
    beforeSend: function(xhr, settings) {
        if (!xsrfSafeMethod(settings.type)) {
        	var token = $('meta[name=_xsrf_token]').attr('content');
          xhr.setRequestHeader("X-XSRF-Token", token);
        }
    }
});

$("#send-verification-email").click(function(event) {
	event.preventDefault();

	$.post('/send_verification_email', 
		function(data) {			
			$("#send-verification-email").remove();
			$("#verification-email-sent-modal").modal();
		});
});

$(document).ready(function() {
	if($("#first_login").length == 1) {
		$.post('/send_verification_email', 
		function(data) {			
			$("#verification-email-sent-modal").modal();
		});
	}
})