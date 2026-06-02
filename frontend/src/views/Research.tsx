import React, { useEffect, useState } from "react";
import {
	ResearchPresenter,
	ResearchView,
} from "../presenters/ResearchPresenter";
import { ResearchGameDTO } from "../../../dtos";

const Research: React.FC = () => {
	const [presenter, setPresenter] = useState<ResearchPresenter | null>(null);
	const [isLoggedIn, setIsLoggedIn] = useState(false);
	const [selectedGame, setSelectedGame] = useState<ResearchGameDTO | null>(
		null,
	);
	const [games, setGames] = useState<ResearchGameDTO[]>([]);
	const getDays = () => {
		if (!selectedGame) return [];

		return Object.entries(selectedGame.data.players);
	};

	useEffect(() => {
		const view: ResearchView = {
			setIsLoggedIn,
			setSelectedGame,
			setGames,
		};
		const researchPresenter = new ResearchPresenter(view);
		setPresenter(researchPresenter);
	}, []);

	if (!presenter) {
		return <div>Loading...</div>;
	}

	const handleLogin = (e: React.FormEvent) => {
		e.preventDefault();
		presenter.handleLogin();
	};

	if (!isLoggedIn) {
		return (
			<div className='card' style={{ maxWidth: "400px", margin: "50px auto" }}>
				<h2 style={{ textAlign: "center" }}>Research Access</h2>
				<form onSubmit={handleLogin}>
					<label>Email</label>
					<input type='email' placeholder='researcher@lab.edu' required />

					<label>Password</label>
					<input type='password' required />

					<button
						type='submit'
						className='btn'
						style={{ width: "100%", marginTop: "10px" }}
					>
						Login
					</button>
				</form>
			</div>
		);
	}

	return (
		<div>
			<h1>Research Dashboard</h1>
			<div style={{ display: "flex", gap: "20px" }}>
				<div className='card' style={{ flex: 1 }}>
					<h3>Game Logs</h3>
					<table style={{ width: "100%", borderCollapse: "collapse" }}>
						<thead>
							<tr style={{ borderBottom: "2px solid #ddd", textAlign: "left" }}>
								<th>ID</th>
								<th>Date</th>
								<th>Rounds</th>
								<th>Action</th>
							</tr>
						</thead>
						<tbody>
							{games.map((g) => (
								<tr key={g.game_id} style={{ borderBottom: "1px solid #eee" }}>
									<td style={{ padding: "10px 0" }}>{g.game_id}</td>
									<td>{new Date(g.created_at).toLocaleString()}</td>
									<td>{g.day_num}</td>
									<td>
										<button
											className='btn btn-secondary'
											style={{ padding: "5px 10px", fontSize: "0.8rem" }}
											onClick={() => presenter.handleSelectGame(g)}
										>
											Analyze
										</button>
									</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>

				<div className="card" style={{ flex: 2 }}>
					{selectedGame ? (
						<div>
							<h3>Game {selectedGame.game_id}</h3>

							<p>
								Day: {selectedGame.day_num} | Phase: {selectedGame.phase}
							</p>

							{Object.entries(selectedGame.data.players).map(
								([day, dayPlayers]: [string, any]) => (
									<div
										key={day}
										style={{
											marginBottom: "20px",
											border: "1px solid #ddd",
											padding: "10px",
											borderRadius: "4px",
										}}
									>
										<h4>Day {day}</h4>

										{Object.entries(dayPlayers).map(
											([playerId, player]: [string, any]) => (
												<div
													key={playerId}
													style={{
														marginBottom: "10px",
														padding: "10px",
														background: "#f7f7f7",
														borderRadius: "4px",
													}}
												>
													<strong>
														{player.name ?? playerId}
													</strong>

													<div>Health: {player.health}</div>

													<div>
														Resources:
														<ul>
															<li>Food: {player.resources?.food ?? 0}</li>
															<li>Wood: {player.resources?.wood ?? 0}</li>
															<li>Iron: {player.resources?.iron ?? 0}</li>
														</ul>
													</div>

													<div>
														Sickness Chance: {player.sickness_chance}
													</div>

													<div>
														Fire Status: {player.fire_status}
													</div>

													<div>
														Actions:
														<pre
															style={{
																maxHeight: "150px",
																overflow: "auto",
															}}
														>
															{JSON.stringify(
																player.actions,
																null,
																2
															)}
														</pre>
													</div>

													<div>
														Committed Action:
														<pre>
															{JSON.stringify(
																player.committed_action,
																null,
																2
															)}
														</pre>
													</div>
												</div>
											)
										)}
									</div>
								)
							)}
						</div>
					) : (
						<p style={{ color: "#888", fontStyle: "italic" }}>
							Select a game to analyze.
						</p>
					)}
				</div>
			</div>
		</div>
	);
};

export default Research;
