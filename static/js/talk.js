moment.lang('ko');
$('#write-talk textarea').autosize();

var dataRef = new Firebase('https://snudate.firebaseIO.com/');
dataRef.auth($("#firebase_token").val());

loadMoreTalks(loadNewTalks);
$("#load-more-talks").click(loadMoreTalks);

function loadMoreTalks(callback) {
  changeLoadingState(true);

  var currentTime = new Date().valueOf();

  if ((lastTalk = $('#talks .talk:last')).length) {
    var lastDisplayTime = lastTalk.find(' .talk-time').attr('title');
    currentTime = moment(lastDisplayTime).valueOf();
  }

  var moreDataQuery = dataRef.child('talks').endAt(currentTime).limit(3);
  moreDataQuery.once('value', function(snapshot) {

    var insertPosition = $('#talkEnd');
    
    //older items are loaded first.
    snapshot.forEach(function (child) {
      var data = child.val();

      displayTalk(data, function(talk) {
        talk.insertBefore(insertPosition); 
        insertPosition = talk;
      });
    });

    changeLoadingState(false);

    if (!snapshot.hasChildren()) {
      $("#load-more-talks").hide();
      $("#no-more-talks").show();
    }

    if (typeof(callback) == typeof(Function)) {
      callback(currentTime);
    }
  });
}

function loadNewTalks(currentTime) {
  var newDataQuery = dataRef.child('talks').startAt(currentTime);
  newDataQuery.on('child_added', function (child) {
    var data = child.val();

    displayTalk(data, function(talk) {
      $('#talks').prepend(talk);
    });
  });
}

function displayTalk(talkData, position) {
  var template = $('#talk-template').clone();
  template.removeAttr("id");
  if(talkData.alias) {
    template.find('.talk-name').text(talkData.alias);
    template.find('.icon-github-alt').show();
  } else {
    template.find('.talk-name').text(talkData.nickname);    
  }

  template.find('.talk-content').text(talkData.content);
  template.find('.talk-time')
           .attr('title', moment(talkData.time).format('YYYY-MM-DD HH:mm:ss'))
           .text(base.getDisplayTime(talkData.time));

  template.find('.add-comment').click(function(e) {
    //talkData.ref().child('/comments').set({})
  })

  position(template);
  template.fadeIn();
};

$('#write-talk-post').click(function (e) {
  var user = getCurrentUser();
  var content = $.trim($('#write-talk-content').val());

  if (user == undefined || content == '')
    return;  

  var currentTime = new Date().getTime();

  var userTalkRef = dataRef.child('users').child(user.username)
                           .push({time:currentTime});

  dataRef.child('talks').child(userTalkRef.name())
                        .set({alias: user.alias,
                              nickname: user.nickname, 
                              content: content,
                              time: currentTime,
                              '.priority': currentTime});


  $('#write-talk-content').val('').trigger('autosize');
});

function getCurrentUser() {
  var nickname = $('#nickname').val();
  var alias = $.trim($('#write-talk-name').val());

  if (nickname == '' && alias == '')
    return undefined;

  if (alias != '' && alias != nickname) { //alias is used.
    nickname = '';
  } else {
    alias = ''; //nickname is used
  }

  var username = $('#username').val();

  return {
    nickname: nickname,
    alias: alias,
    username: username
  }
}

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
      $(this).text(base.getDisplayTime(time));  
    }    
  });
}, 60 * 1000)