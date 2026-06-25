"""
Lightweight SVG knockout-progression visual: shows top contenders'
probability of reaching each round, ending in the predicted winner.
Doesn't hardcode an actual bracket draw (that depends on group results
that haven't been played) — instead it's a "road to the final" funnel,
which is what the handoff doc asks for ("round reach probabilities",
"favorite route to the final") ahead of real fixtures existing.
"""

ROUNDS = ["round_of_32", "round_of_16", "quarterfinal", "semifinal", "final", "tournament_win_probability"]
ROUND_LABELS = ["Round of 32", "Round of 16", "Quarterfinal", "Semifinal", "Final", "Winner"]


def build_funnel_svg(round_reach_df, top_n: int = 8) -> str:
    df = round_reach_df.head(top_n).reset_index(drop=True)
    row_h = 42
    header_h = 50
    label_col_w = 190
    col_w = 90
    width = label_col_w + col_w * len(ROUNDS) + 20
    height = header_h + row_h * len(df) + 20

    svg = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
           f'style="width:100%; height:auto; font-family:inherit;">']
    svg.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="transparent"/>')

    # column headers
    for i, label in enumerate(ROUND_LABELS):
        x = label_col_w + i * col_w + col_w / 2
        svg.append(f'<text x="{x}" y="28" text-anchor="middle" font-size="11" '
                    f'fill="currentColor" opacity="0.7" font-weight="600">{label}</text>')

    max_val = max(df["round_of_32"].max(), 0.01)
    for r, team_row in df.iterrows():
        y = header_h + r * row_h + row_h / 2
        flag_size = 16
        svg.append(f'<image href="{team_row["flag_url"]}" x="6" y="{y - flag_size/2:.1f}" '
                    f'width="{flag_size*1.4:.0f}" height="{flag_size}" preserveAspectRatio="xMidYMid slice"/>')
        svg.append(f'<text x="{6 + flag_size*1.4 + 6:.0f}" y="{y + 4}" font-size="13" fill="currentColor" '
                    f'font-weight="600">{team_row["team"]}</text>')
        for i, col in enumerate(ROUNDS):
            val = team_row[col]
            x = label_col_w + i * col_w + col_w / 2
            radius = 6 + 12 * (val / max_val) ** 0.5
            opacity = 0.35 + 0.65 * (val / max_val)
            color = "#2e9e5b" if col != "tournament_win_probability" else "#d4af37"
            svg.append(f'<circle cx="{x}" cy="{y}" r="{radius:.1f}" fill="{color}" opacity="{opacity:.2f}"/>')
            pct_label = f"{val * 100:.0f}%" if val >= 0.01 else "<1%"
            svg.append(f'<text x="{x}" y="{y + 3}" text-anchor="middle" font-size="9.5" '
                        f'fill="#0b0b0b" font-weight="600">{pct_label}</text>')

    svg.append("</svg>")
    return "\n".join(svg)
