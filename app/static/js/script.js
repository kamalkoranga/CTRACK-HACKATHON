async function follow_user(data, username) {
  try {
    const response = await fetch(`/follow/${username}`);
    if (!response.ok) {
      throw new Error('Request failed.');
    }

    if (data == "profile") {
      document.querySelector('.followers_count').innerHTML++;
    }

  } catch (error) {
    console.log(error);
  }
  // console.log('followed');
}

async function unfollow_user(data, username) {
  try {
    const response = await fetch(`/unfollow/${username}`);
    if (!response.ok) {
      throw new Error('Request failed.');
    }

    if (data == "profile") {
      document.querySelector('.followers_count').innerHTML--;
    }

  } catch (error) {
    console.log(error);
  }
  // console.log('unfollowed');
}

function follow_unfollow(data, username) {
  if (data == 'profile') {
    // This case will only run when the follow button in profile page section 
    // clicked ..
    const follow_btn = document.querySelector('#follow');
    const unfollow_btn = document.querySelector('#unfollow');

    if (follow_btn) {
      follow_btn.className = "btn btn-outline-primary rounded-pill px-3 fw-bold";
      follow_btn.innerHTML = `<i class="fa-solid fa-check"></i> Following`;
      follow_btn.id = "unfollow";
      follow_user('profile', username);

    } else {
      unfollow_btn.className = "btn btn-primary rounded-pill px-3 fw-bold";
      unfollow_btn.innerHTML = `<i class="fa-solid fa-plus"></i> Follow`;
      unfollow_btn.id = "follow";
      unfollow_user('profile', username);
    }
  }

  else {
    /* THIS IS FOR FOLLOWINNG/UNFOLLOWING USER FROM SUGGESTION SECTION IN PROFILE PAGE
     * This case will run when button in suggestions section of profile
     * page is clicked.
     *  -> 'data' will be user_id
     */
    const follow_btn = document.querySelector(`#follow-${data}`);
    const unfollow_btn = document.querySelector(`#unfollow-${data}`);

    if (follow_btn) {
      follow_btn.className = "btn btn-outline-secondary rounded-pill px-3 fw-bold mt-2";
      follow_btn.innerHTML = `<i class="fa-solid fa-check"></i> Following`;
      follow_btn.id = `unfollow-${data}`;
      follow_user('profile__suggestions', username);

    } else {
      unfollow_btn.className = "btn btn-outline-secondary rounded-pill px-3 fw-bold mt-2";
      unfollow_btn.innerHTML = `<i class="fa-solid fa-plus"></i> Follow`;
      unfollow_btn.id = `follow-${data}`;
      unfollow_user('profile__suggestions', username);
    }
  }
}

/**
     * Like function for updating class names of i and span tags without refreshing webpage
     *
     * @param {number} postId - The ID of the post to be liked.
     */
function like(postId) {
  // Get the necessary elements for updating the like status
  const likeCount = document.getElementById(`likes-count-${postId}`);
  const likeButton = document.getElementById(`like-button-${postId}`);
  const likeSpan = document.getElementById(`like-span-${postId}`);

  if (likeSpan.classList.contains('text-primary')) {
    likeCount.innerHTML = Number(likeCount.innerHTML) - 1;
    likeSpan.classList = "text-secondary px-1";
    likeButton.className = "fas fa-thumbs-up fa-xl fa-flip-horizontal";
  } else {
    likeCount.innerHTML = Number(likeCount.innerHTML) + 1;
    likeSpan.classList = "text-primary px-1";
    likeButton.className = "fas fa-thumbs-up fa-xl fa-flip-horizontal";

  }

  // Send a POST request to the server to like the post
  fetch(`/like_post/${postId}`, { method: "POST" })
    // .then((res) => res.json()) // Parse the response as JSON
    // .then((data) => {
    //     // Updating the like count and visual styles class based on the response data
    //     likeCount.innerHTML = data["likes"];
    //     if (data["liked"] === true) {
    //         // likeButton.className = "fas fa-thumbs-up fa-xl fa-flip-horizontal text-primary";
    //         // likeSpan.className = "text-primary"
    //     } else {
    //         // likeButton.className = "far fa-thumbs-up fa-xl fa-flip-horizontal text-secondary";
    //         // likeSpan.className = "text-secondary"
    //     }
    // })
    // Display an error message if the request fails
    .catch((e) => alert("Could not like post."));
}


function open_comments(post_id) {
  /*
   * This function is responsible for opening comment-section and all-comment section
   * when a user clicked like button or comment button as same as linkedin :)
  */
  const comment_section = document.querySelector(`#comment-section-${post_id}`);
  const all_comment = document.querySelector(`#all-comment-${post_id}`);
  comment_section.className = "comment-section d-flex align-items-start gap-2 mx-3 mb-3 d-block";
  all_comment.className = "all-comments d-block";
}



function open_post_btn(post_id) {
  /*
   * This function is used for automatically opening and closing post button when
   * user inputs any value in form.
  */
  const comment_textarea = document.querySelector(`#comment-textarea-${post_id}`);
  const comment_post = document.querySelector(`#comment-post-${post_id}`);

  comment_textarea.addEventListener("input", function () {
    if (comment_textarea.value !== "") {
      comment_post.style.display = "inline";
    } else {
      comment_post.style.display = "none";
    }
  });

}


function add_comment(post_id) {
  /*
   * This functions is the most important function for appending comment in all-comments section and then sends
   * comment data to server using POST request
  */

  const comment = document.querySelector(`#comment-textarea-${post_id}`).value;
  const all_comment = document.querySelector(`#all-comment-${post_id}`);
  const comment_div = document.createElement('div');
  const comment_img = `<img src="{{current_user.gravatar(size=256)}}" alt="" class="profile">`;
  const comment_div2 = document.createElement('div');
  const card_body = `
        <div class="card-body">
            <a
                class="body-top d-flex justify-content-start align-items-center gap-2 position-relative mb-2 link-underline link-underline-opacity-0"
                href="{{url_for('main.user', username=current_user.username)}}">
                <i class="fa-solid fa-ellipsis position-absolute top-0 end-0 post-menu"></i>
                <div class="d-flex flex-column post-top">
                    <span class="text-secondary fs-6">
                        <strong>{{ current_user.name }}</strong> • 3rd+
                    </span>
                    {% if current_user.headline %}
                    <p class="text-secondary m-0">{{
                        current_user.headline[:70] }}{% if
                        current_user.headline|length > 70 %}...{% endif %}
                    </p>
                    {% endif %}
                    <p class="text-secondary m-0">
                        a few seconds ago • <i class="fa-solid fa-earth-asia"></i>
                    </p>
                </div>
            </a>
            <p class="comment__text m-0">${comment}</p>
        </div>
        `

  comment_div.className = "comment d-flex gap-2 align-items-start mx-3 mb-3";
  comment_div2.className = "card comment__card w-100";

  comment_div2.innerHTML = card_body;
  comment_div.innerHTML = comment_img;
  comment_div.appendChild(comment_div2);
  all_comment.prepend(comment_div);
  document.querySelector(`.comments-${post_id}`).innerHTML++;
  document.querySelector(`#comment-textarea-${post_id}`).value = "";
  add_comment_to_db(comment, post_id)
}

async function add_comment_to_db(comment, post_id) {
  try {
    const data = {
      body: comment,
      post_id: post_id,
    };
    const response = await fetch(`/add_comment/${post_id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    if (response.ok) {
      const responseData = await response.json();
    } else {
      throw new Error('Request failed.');
    }
  } catch (error) {
    console.log(error);
  }
}