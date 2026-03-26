import React from "react";
import { MessageDTO } from "../../../../dtos";

interface Props {
	msg: MessageDTO;
}

const ChatMessage: React.FC<Props> = ({ msg }) => {
	return <span>{msg.content}</span>;
};

export default ChatMessage;
