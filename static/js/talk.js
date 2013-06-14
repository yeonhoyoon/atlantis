moment.lang('ko');
$('#write-talk textarea').autogrow();

var dataRef = new Firebase('https://snudate.firebaseIO.com/');

var oldDataQuery = dataRef.child('talks').limit(3);
var newDataQuery = dataRef.child('talks').startAt(new Date().valueOf());

dataRef.auth($("#firebase_token").val());

oldDataQuery.once('value', function (snapshot) {
  changeLoadingState(false);

  snapshot.forEach(function (child) {
    var data = child.val();

    displayTalk(data, function(talk) {
      $('#talks').prepend(talk);
    });
  });
});

newDataQuery.on('child_added', function (child) {
  var data = child.val();

  displayTalk(data, function(talk) {
    $('#talks').prepend(talk);
  });
});

function displayTalk(talk, position) {
  var template = $('#talk-template').clone();
  $(template).removeAttr("id");
  if(talk.alias) {
    $(template).find('.talk-name').text(talk.alias);
    $(template).find('.icon-ok-circle').hide();
  } else {
    $(template).find('.talk-name').text(talk.nickname);    
  }

  $(template).find('.talk-content').text(talk.content);
  $(template).find('.talk-time')
             .attr('title', moment(talk.time).format('YYYY-MM-DD HH:mm:ss'))
             .text(getDisplayTime(talk.time));

  position(template);
  template.fadeIn();
};

function getDisplayTime(time) {
  if(moment(time).isBefore(moment().subtract('days', 1))) {
    return moment(time).calendar();
  } else {
    return moment(time).fromNow();
  }
}

$('#write-talk-post').click(function (e) {
  var nickname = $('#nickname').val();
  var alias = $.trim($('#write-talk-name').val());
  var content = $.trim($('#write-talk-content').val());

  if((nickname == '' && alias == '') || content == '')
    return;

  if(alias != '' && alias != nickname) { //alias is used.
    nickname = '';
  } else {
    alias = ''; //nickname is used
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

$("#load-more-talks").click(function (e) {
  changeLoadingState(true);

  var lastTalk = $('#talks .talk:last-child');
  var lastTime = lastTalk.find(' .talk-time').attr('title');

  var moreDataQuery = dataRef.child('talks').endAt(moment(lastTime).valueOf()).limit(3);
  moreDataQuery.once('value', function(snapshot) {
    snapshot.forEach(function (child) {
      var data = child.val();

      displayTalk(data, function(talk) {
        talk.insertAfter(lastTalk);
      });
    });

    changeLoadingState(false);

    if (!snapshot.hasChildren()) {
      $("#load-more-talks").hide();
      $("#no-more-talks").show();
    }
  });
});

function changeLoadingState(isLoading) {
  if (isLoading) {
    $('#spinner').show();
    $('#load-more-talks').hide();
  } else {
    $('#spinner').hide();
    $('#load-more-talks').show();
  }
}

setInterval(function() {
  $("#talks .talk-time").each(function () {
    var time = $(this).attr('title');
    if (time !== undefined) {
      $(this).text(getDisplayTime(time));  
    }    
  });
}, 60 * 1000)