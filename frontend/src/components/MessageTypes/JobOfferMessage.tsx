import React from "react";
import { MessageDTO } from "../../../../dtos";

interface Props {
	msg: MessageDTO;
	isEditing: boolean;
	barterValues: Partial<MessageDTO>;
	setBarterValues: (values: Partial<MessageDTO>) => void;
}

const JobOfferMessage: React.FC<Props> = ({
	msg,
	isEditing,
	barterValues,
	setBarterValues,
}) => {
	const inputStyle = { width: "70px", padding: "4px", marginRight: "4px" };
	const selectStyle = { padding: "4px", marginRight: "4px" };

	if (isEditing) {
		return (
			<div style={{ display: "flex", gap: "5px", alignItems: "center" }}>
				<span>Offer:</span>
				<input
					type='number'
					style={inputStyle}
					value={barterValues.wage_offer}
					onChange={(e) =>
						setBarterValues({
							...barterValues,
							wage_offer: Number(e.target.value),
						})
					}
				/>
				<select
					style={selectStyle}
					value={barterValues.wage_type}
					onChange={(e) =>
						setBarterValues({
							...barterValues,
							wage_type: e.target.value,
						})
					}
				>
					<option value='food'>Food</option>
					<option value='wood'>Wood</option>
					<option value='iron'>Iron</option>
				</select>
			</div>
		);
	}

	return (
		<span>
			<strong>Job:</strong> Work for {msg.wage_offer} {msg.wage_type}
		</span>
	);
};

export default JobOfferMessage;
