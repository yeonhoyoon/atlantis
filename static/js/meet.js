$(".userCard a.select").click(function(event) {
	var currentCard = $(this).parents(".userCard");
	var profile_uuid = currentCard.find(".profile-uuid").attr("value");
	var isSelected = getSelectedCard(profile_uuid).length > 0;

	if (!isSelected && getSelectedUserCount() == 3) {
		$("#noRemainingChoicesAlert").show();
		return;		
	}

	if (!isSelected) {
		styleSelect(currentCard);

		$("#selectedUsers .unknownCard:visible:last").hide();
		var selectedCard = currentCard.clone(true)
																	.insertBefore(".unknownCard:first").hide();
		colorizeLabels(selectedCard);

		selectedCard.show(0, refreshRemainingChoices);
	} 
	else {
		var selectedCard = getSelectedCard(profile_uuid);
		selectedCard.hide(0, function () {
			selectedCard.remove();
			$("#selectedUsers .unknownCard:hidden:last").show();
			refreshRemainingChoices();
		});
		var matchingUserCard = getUserCardFromUserPool(profile_uuid);
		styleUnselect(matchingUserCard);

		$("#noRemainingChoicesAlert").hide();
	}
});

function refreshRemainingChoices() {
	$("#remainingChoices .number").text(3 - getSelectedUserCount());	
}

function getUserCardFromUserPool(profile_uuid) {
	return $("#userPool .userCard").has(".profile-uuid[value=" + profile_uuid + "]");
}

function getSelectedCard(profile_uuid) {
	return $("#selectedUsers .userCard").has(".profile-uuid[value=" + profile_uuid + "]");
}

function getSelectedUserCount() {
	return $("#selectedUsers .userCard").length;
}

function styleSelect(card) {
	var icon = card.find("i"); 
	icon.removeClass("icon-star-empty").addClass("icon-star");
}

function styleUnselect(card) {
	var icon = card.find("i"); 
	icon.removeClass("icon-star").addClass("icon-star-empty");
}

function colorizeLabels(card) {
	var labels = card.find(".label").removeClass("label-default");
		$(labels[0]).addClass("label-info");
		$(labels[1]).addClass("label-warning");
  	$(labels[2]).addClass("label-success");
}