function format_chatstream(chatstream, sender_id) {

  let chat_box = document.createElement('div'); chat_box.classList.add('chat-box');
  let text = "";

  // split on sender IDs and recipients
  let groups = [];
  let group;

  let last_sender = "";
  let last_recipient = "";
  for (let chat of chatstream) {
    if (last_sender != chat.sender_id || last_recipient != chat.recipient_id) {
      last_sender = chat.sender_id;
      last_recipient = chat.recipient_id;
      group = {
        'sender_id':chat.sender_id,
        'sender_name':chat.sender_name,
        'recipient_id':chat.recipient_id,
        'recipient_name':chat.recipient_name,
        'chats':[]
      };
      groups.push(group);
    }
    group.chats.push(chat);
  }

  for (let group of groups) {
    let bubble_group = document.createElement('div'); bubble_group.classList.add('bubble-group');
    let name = document.createElement('p'); name.classList.add('name');
    name.innerHTML = group.sender_id == sender_id ? 'You' : group.sender_name;

    let span = document.createElement('span');
    span.innerHTML = group.recipient_id == sender_id ? 'You' : group.recipient_name;
    if (group.recipient_id != 'everyone') {
      span.style.color = 'red';
    }
    name.appendChild(document.createTextNode(' to '));
    name.appendChild(span);

    text +=  group.sender_name + " to " + group.recipient_name + "\n";

    bubble_group.appendChild(name);

    for (let chat of group.chats) {
      let bubble_container = document.createElement('div'); bubble_container.classList.add('bubble-container');
      let bubble = document.createElement('div'); bubble.classList.add('bubble');
      bubble.appendChild(document.createTextNode(chat.message));

      text += "\t[" + new Date(1000 * chat.time).toUTCString() + "]: \"" + chat.message + "\"\n";

      if (group.recipient_id != 'everyone') {
        bubble.classList.add('private');
      }

      if (chat.sender_id == sender_id) {
        bubble.classList.add('bubble-right');
        name.classList.add('name-right');
      } else {
        bubble.classList.add('bubble-left');
        name.classList.add('name-left');
      }

      bubble_container.appendChild(bubble);
      bubble_group.appendChild(bubble_container);

    }

    chat_box.appendChild(bubble_group);
  }

  return [chat_box, text];
}
