# Writing a blog post with code and data

A guide for Deliverome scientists, no coding experience needed. Claude does the git and
code work; you bring the science.

## The two repositories

| Repo | Who sees it | What it's for |
|---|---|---|
| `deliverome-blog-drafts` | Deliverome only (private) | **Where you work.** Messy is fine: half-finished data, rough figures, experiments. |
| `deliverome-blog` | Everyone (public) | The finished, citable version of each post, added when the post goes live. |

The drafts repo stays in sync with the public one automatically every night. When your
post is ready, one step copies *just your post's folder* to the public repo as a clean
copy. Your drafts history never becomes public.

## One-time setup

1. Make sure you're in the `Deliverome-Project` GitHub organization (ask Becca).
2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and the GitHub CLI
   (`brew install uv gh`), then run `gh auth login`.
3. Get a copy of the drafts repo:

   ```bash
   gh repo clone Deliverome-Project/deliverome-blog-drafts ~/git/deliverome-blog-drafts
   ```

4. In Claude Desktop, open the **Code** tab and choose the `deliverome-blog-drafts`
   folder. Claude reads the repo's instructions (`CLAUDE.md`) and knows the conventions.

## Writing your post

Ask Claude in plain words. For example:

- *"Start a new post called 'Optimizing lentivirus production' by Maria ter Weele."*
- *"Here is my protocol (attach the doc). Turn it into `protocol/protocol.md` and the
  reagent list."*
- *"These are my titer measurements (attach the spreadsheet). Make a figure of functional
  titer versus plasmid ratio."*
- *"Make the y-axis log scale and label it TU/mL."*
- *"Save my work."* (Claude commits it to the drafts repo.)

Every figure gets its own small script that rebuilds it exactly, so a reader can check
your numbers. You don't need to read the scripts; just check the figures look right.

**Large data** (anything over about 25 MB, like flow `.fcs` files or images): give Claude
the folder and say it's large. It goes in `data/external/`, which is never committed;
when the post is published it's uploaded to Zenodo with a DOI.

## Never put in either repo

- Patient or donor identifiers, or names in sample sheets
- Passwords, tokens, or `.env` files
- Results that aren't part of this post, or internal Notion/Slack/ELN links

If you're unsure, ask Becca before saving.

## Publishing

1. When the post is final, ask Claude: *"Promote my post to the public repo."* That opens
   a pull request on the public repo, which runs the checks. Nothing is public until it
   is merged.
2. When the Substack post goes live, the PR is merged and the post gets its own release
   with a citable DOI (Becca or Claude does this; see "Releasing a post" in `CLAUDE.md`).
3. Corrections later: fix it in drafts, then promote again. The public PR shows exactly
   what changed.
