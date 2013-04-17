$("a.favorite").click(function() {
	$(this).find("i").removeClass("icon-star-empty");
	$(this).find("i").addClass("icon-star");
});