(function(talklogic, $, moment, base, undefined) {
moment.lang('ko');
$('#write-talk textarea').autosize();

var dataRef = new Firebase('https://snudate.firebaseIO.com/');
dataRef.auth($("#firebase_token").val());

loadMoreTalks(loadNewTalks);
$("#load-more-talks").click(loadMoreTalks);

var user = getCurrentUser();
$("#write-talk-name").change(function () {
  user = getCurrentUser();
});

function loadMoreTalks(callback) {
  changeLoadingState(true);

  var currentTime = moment().valueOf();

  if ((lastTalk = $('#talks .talk:last')).length) {
    var lastDisplayTime = lastTalk.find(' .talk-time').attr('title');
    currentTime = moment(lastDisplayTime).valueOf();
  }

  var moreDataQuery = dataRef.child('talks').endAt(currentTime).limit(3);
  moreDataQuery.once('value', function(snapshot) {

    var insertPosition = $('#talkEnd');
    
    //older items are loaded first.
    snapshot.forEach(function (child) {
      displayTalk(child, function(talk) {
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
    displayTalk(child, function(talk) {
      $('#talks').prepend(talk);
    });
  });
}

function displayTalk(talk, position) {
  var talkData = talk.val();
  var template = $('#talk-template').clone();
  template.removeAttr("id");
  if(talkData.alias) {
    template.find('.talk-name').text(talkData.alias);
    template.find('.talk-alias').show();
  } else {
    template.find('.talk-name').text(talkData.nickname);    
  }

  template.find('.talk-content').text(talkData.content);
  template.find('.talk-time')
           .attr('title', moment(talkData.time).format('YYYY-MM-DD HH:mm:ss'))
           .text(base.getDisplayTime(talkData.time));

  prepareComments(talk, template);
  position(template);
  template.fadeIn();
};

$('#write-talk-post').click(function (e) {
  var content = $.trim($('#write-talk-content').val());

  if (user == undefined || content == '')
    return;  

  var currentTime = moment().valueOf();

  var userTalkRef = dataRef.child('users/' + user.username + '/talks')
                           .push({time:currentTime});

  dataRef.child('talks/' + userTalkRef.name()).set({
    alias: user.alias,
    nickname: user.nickname,
    content: content,
    time: currentTime,
    '.priority': currentTime
  });

  $('#write-talk-content').val('').trigger('autosize');
});

function prepareComments(talk, template) {
  var commentsSection = template.find('.comments');
  template.find('.show-comment').click(function(e) {
    commentsSection.toggle();
  });

  var writeCommentArea = $(commentsSection).find(".write-comment-area");
  var position = function(comment) {
    comment.insertBefore(writeCommentArea);
  }

  var currentTime = moment().valueOf();
  loadOldComments(talk.name(), position, function() {
    loadNewComments(talk.name(), position, currentTime);
  });

  //add post comment event handlers(enter, click)
  var contentEl = template.find('.write-comment-content').autosize();
  contentEl.keydown(function(event) {
    if(isEnter(event)) {
      postComment(contentEl, talk);

      event.preventDefault();
    }
  });
  
  template.find('.write-comment-post').click(function(event) {
    postComment(contentEl, talk)
  });
}

function loadOldComments(talkName, position, callback) {
  var oldCommentsQuery = dataRef.child('comments/' + talkName);
  oldCommentsQuery.once('value', function(snapshot) {
    snapshot.forEach(function(child) {
      displayComment(child.val(), position);
    });

    if (typeof(callback) == typeof(Function)) {
      callback();
    } 
  });
}

function loadNewComments(talkName, position, currentTime){
  var newCommentsQuery = dataRef.child('comments/' + talkName).startAt(currentTime);
  newCommentsQuery.on('child_added', function(child) {
      displayComment(child.val(), position); 
  }); 
}

function displayComment(commentData, position) {
  var template = $('#comment-template').clone();
  template.removeAttr("id");
  if(commentData.alias) {
    template.find('.comment-name').text(commentData.alias);
    template.find('.comment-alias').show();
  } else {
    template.find('.comment-name').text(commentData.nickname);    
  }

  template.find('.comment-content').text(commentData.content);
  template.find('.comment-time')
           .attr('title', moment(commentData.time).format('YYYY-MM-DD HH:mm:ss'))
           .text(base.getDisplayTime(commentData.time));

  position(template);
  refreshCommentsCount(template);
  template.fadeIn('fast');
}

function refreshCommentsCount(comment) {
  var parentTalk = comment.closest('.talk');

  if (commentsCount = parentTalk.find('.comment').length) {
    var showCommentsText = parentTalk.find('.show-comment-text');
    showCommentsText.text('댓글 ' + commentsCount + '개');
  }
}

function postComment(textArea, talk){
  var content = $.trim($(textArea).val());

  if(user == undefined || content == '')
    return;

  var currentTime = moment().valueOf();

  var userCommentRef = dataRef.child('users/' + user.username + '/comments')
                              .push({time:currentTime});

  dataRef.child('comments/' + talk.name() + '/' + userCommentRef.name()).set({
    alias: user.alias,
    nickname: user.nickname,
    content: content,
    time: currentTime,
    '.priority': currentTime
  });

  $(textArea).val('').trigger('autosize');
}

function isEnter(event) {
  return event.keyCode == 13 && !event.shiftKey && !event.ctrlKey;
}

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

}(window.talklogic = window.talklogic || {}, jQuery, moment, base));