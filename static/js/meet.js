(function meetlogic(meetlogic, $, moment, undefined){

$(".user-card a.select").click(function() {
	var currentCard = $(this).parents(".user-card");
	var profile_uuid = currentCard.find(".profile-uuid").attr("value");
	var isSelected = getSelectedCard(profile_uuid).length > 0;

	if (!isSelected && getSelectedUserCount() == 3) {
		$("#no-remaining-choices-alert").show();
		return;		
	}

	if (!isSelected) {
		styleSelect(currentCard);

		$("#selected-users .unknown-card:visible:last").hide();
		var selectedCard = currentCard.clone(true)
																	.insertBefore(".unknown-card:first");
	} 
	else {
		var selectedCard = getSelectedCard(profile_uuid);
		selectedCard.hide(); 
		selectedCard.remove();
		$("#selected-users .unknown-card:hidden:last").show();
		
		var matchingUserCard = getUserCardFromUserCardpool(profile_uuid);
		styleUnselect(matchingUserCard);

		$("#no-remaining-choices-alert").hide();
	}
});

$("#show-summary").click(function (event) {
	event.preventDefault();

	var selected_profile_uuids = $("#selected-users .user-card .profile-uuid")
																	.map(function() { return this.value }).get(); 

	if(selected_profile_uuids.length == 0) {
		var firstCard = $(".unknown-card:first-child").find("a");
		firstCard.clickover('show');
		setTimeout(function() {firstCard.clickover('hide')}, 3*1000);
		return;
	}
	
	$.post('/meet/show_summary', 
		{ selected_profile_uuids: selected_profile_uuids }, 
		function(data) {
			window.location.replace("/meet");
		});
});

$(".show-profile").click(function (event) {
event.preventDefault();

var profile_uuid = $(this).parents(".user-card").find(".profile-uuid").attr("value");

	$.post('/meet/show_profile', 
		{ profile_uuid: profile_uuid }, 
		function(data) {
			window.location.replace("/meet");
		});
});

$("#propose").click(function (event) {
	event.preventDefault();

	var profile_uuid = $("#show-profile-body").find(".profile-uuid").attr("value");

	$.post('/meet/propose', 
		{ profile_uuid: profile_uuid }, 
		function(data) {
			window.location.replace("/meet");
		});
});

$(".unknown-card a[rel=clickover]").clickover({ placement: 'bottom' });

function getUserCardFromUserCardpool(profile_uuid) {
	return $("#user-pool .user-card").has(".profile-uuid[value=" + profile_uuid + "]");
}

function getSelectedCard(profile_uuid) {
	return $("#selected-users .user-card").has(".profile-uuid[value=" + profile_uuid + "]");
}

function getSelectedUserCount() {
	return $("#selected-users .user-card").length;
}

function styleSelect(card) {
	var icon = card.find("i"); 
	icon.removeClass("icon-star-empty").addClass("icon-star");
}

function styleUnselect(card) {
	var icon = card.find("i"); 
	icon.removeClass("icon-star").addClass("icon-star-empty");
}

//Comments
$("#write-comment-content").keydown(handleEnter).autosize();
$("#write-comment-post").click(postComment);

updateCommentsTime();

function handleEnter(event) {
    if (event.keyCode == 13 && !event.shiftKey && !event.ctrlKey) {
    	postComment();
    	return false;
    }
}

function postComment(textareaElement) {
	var commentArea = $("#write-comment-content");
	var proposal_key_str = $('#proposal-key-str').val();
	var content = commentArea.val();

	$.post('/meet/add_comment', 
		{ proposal_key_str: proposal_key_str,
			content: content }, 
		function(data) {
			$("#comments").html(data);
			commentArea.val('');
			commentArea.trigger('autosize');
			updateCommentsTime();
		});
}

function updateCommentsTime() {
	$("#comments .comment-time").each(function () {
  var time = moment($(this).attr('title'));
  if (time !== undefined) {
    $(this).text(base.getDisplayTime(time));  
  }    
	});
}


}(window.meetlogic = window.meetlogic || {}, jQuery, moment));