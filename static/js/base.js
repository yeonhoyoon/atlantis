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
});

//UserVoice
(function(){
	var uv=document.createElement('script');
	uv.type='text/javascript';
	uv.async=true;
	uv.src = 'http://widget.uservoice.com/uAOMxL0DtcC70Gd16y4Q.js';
	var s=document.getElementsByTagName('script')[0];
	s.parentNode.insertBefore(uv,s)})()

UserVoice = window.UserVoice || [];
function showClassicWidget() {
  UserVoice.push(['showLightbox', 'classic_widget', {
    mode: 'full',
    primary_color: '#cc6d00',
    link_color: '#007dbf',
    default_mode: 'feedback',
    forum_id: 203699,
    support_tab_name: '1:1 문의',
    feedback_tab_name: '제안합니다'
  }]);
}

$("#feedback-link").click(function() {
	showClassicWidget();
});