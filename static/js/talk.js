$('#write-talk textarea').autogrow();

var dataRef = new Firebase('https://snudate.firebaseIO.com/');

var oldDataQuery = dataRef.child('talks').limit(10);
var newDataQuery = dataRef.child('talks').startAt(new Date().getTime());

dataRef.auth($("#firebase_token").val());

oldDataQuery.once('value', function (snapshot) {
  $('#spinner').hide();

  snapshot.forEach(function (child) {
    var talk = child.val();
    displayTalkMessage(talk, false);
  });
});

newDataQuery.on('child_added', function (child) {
  var talk = child.val();
  displayTalkMessage(talk, true);
});

function displayTalkMessage(talk, isSlow) {
  var template = $('#talk-template').clone();
  $(template).removeAttr("id");
  if(talk.alias) {
    $(template).find('.talk-name').text(talk.alias);
    $(template).find('.icon-ok-circle').hide();
  }
  else {
    $(template).find('.talk-name').text(talk.nickname);    
  }

  $(template).find('.talk-content').text(talk.content);
  $(template).find('.talk-time').text(moment(talk.time).format('h:mm:ss a'));

  $('#talks').prepend(template);

  if (isSlow) {
    template.show('slow');
  }
  else {
    template.show();
  }
};

$('#write-talk-post').click(function (e) {
  var nickname = $('#nickname').val();
  var alias = $.trim($('#write-talk-name').val());
  var content = $.trim($('#write-talk-content').val());

  if((nickname == '' && alias == '') || content == '')
    return;

  if(alias != '' && alias != nickname) { //alias is used.
    nickname = '';
  }
  else {
    alias = '';
  }

  var username = $('#username').val();
  var currentTime = new Date().getTime();

  var userTalkRef = dataRef.child('users').child(username).push({time:currentTime});


  dataRef.child('talks').child(userTalkRef.name())
                       .set({alias: alias,
                             nickname: nickname, 
                             content: content, 
                             time: currentTime,
                             '.priority': currentTime});


  $('#write-talk-content').val('');
});