"""Reddit lead generation CLI command."""

import asyncio

import click
from tqdm import tqdm

from src.search.adapters.reddit import RedditAdapter
from src.extraction.reddit_lead_extractor import RedditLeadExtractor
from src.storage.checkpoint import CheckpointService
from src.core.signals import setup_signal_handlers, set_cleanup_callback


@click.command(name="reddit")
@click.option(
    "--subreddit", "-r", required=True, help="Subreddit to search (without r/)"
)
@click.option("--query", "-q", help="Search query within subreddit")
@click.option(
    "--sort",
    type=click.Choice(["hot", "new", "top", "rising"]),
    default="hot",
    help="Sort order",
)
@click.option(
    "--time",
    type=click.Choice(["hour", "day", "week", "month", "year", "all"]),
    default="month",
    help="Time filter",
)
@click.option("--limit", default=50, help="Max posts to process (default: 50)")
@click.option("--category", help="Business category label for leads")
@click.option(
    "--require-email-and-phone",
    is_flag=True,
    default=False,
    help="Only save leads with both email AND phone",
)
@click.option(
    "--delay", default=1.0, help="Delay between requests in seconds (default: 1.0)"
)
@click.option("--dry-run", is_flag=True, default=False, help="Preview without saving")
def reddit(
    subreddit,
    query,
    sort,
    time,
    limit,
    category,
    require_email_and_phone,
    delay,
    dry_run,
):
    """Search Reddit for business leads.

    Searches Reddit posts for contact info like emails, websites, and phone numbers.
    No API key required — uses Reddit's public JSON API.

    Examples:

    \b
        # Search r/forhire for leads
        lead-gen reddit -r forhire --limit 50

    \b
        # Search r/smallbusiness for web development leads
        lead-gen reddit -r smallbusiness -q "need website" --sort new --limit 30

    \b
        # Search r/entrepreneur with email+phone requirement
        lead-gen reddit -r entrepreneur --require-email-and-phone --limit 100
    """
    asyncio.run(
        _run_reddit(
            subreddit,
            query,
            sort,
            time,
            limit,
            category,
            require_email_and_phone,
            delay,
            dry_run,
        )
    )


async def _run_reddit(
    subreddit,
    query,
    sort,
    time_filter,
    limit,
    category,
    require_email_and_phone,
    delay,
    dry_run,
):
    """Execute Reddit search asynchronously."""

    if dry_run:
        click.echo("=== DRY RUN MODE ===")
        click.echo(f"Subreddit: r/{subreddit}")
        click.echo(f"Query: {query or '(all posts)'}")
        click.echo(f"Sort: {sort}")
        click.echo(f"Time filter: {time_filter}")
        click.echo(f"Limit: {limit} posts")
        click.echo(f"Require email+phone: {require_email_and_phone}")
        click.echo("=====================")
        return

    adapter = RedditAdapter(delay=delay)
    extractor = RedditLeadExtractor()
    checkpoint_service = CheckpointService()

    job_id = f"reddit_{subreddit}_{query or 'all'}_{sort}"

    # Set up signal handlers for graceful shutdown
    def save_checkpoint():
        try:
            checkpoint_service.save_progress(
                "reddit", job_id, completed_ids, [], "interrupted"
            )
        except Exception:
            pass

    setup_signal_handlers(save_checkpoint)
    set_cleanup_callback(save_checkpoint)

    # Check for resumable checkpoint
    completed_ids = []
    if checkpoint_service.is_resumable("reddit", job_id):
        checkpoint = checkpoint_service.load_checkpoint("reddit", job_id)
        if checkpoint:
            completed_ids = checkpoint.get("completed_items") or []
            click.echo(
                f"Resuming from checkpoint... {len(completed_ids)} posts already processed."
            )

    click.echo(f"Searching r/{subreddit}{' for: ' + query if query else ''}...")
    click.echo(f"Sort: {sort} | Time: {time_filter} | Limit: {limit}")
    click.echo()

    try:
        posts = await adapter.search_subreddit(
            subreddit=subreddit,
            query=query or "",
            sort=sort,
            time_filter=time_filter,
            limit=limit,
        )
    except Exception as e:
        raise click.ClickException(f"Failed to fetch posts: {e}")

    if not posts:
        click.echo("No posts found.")
        return

    click.echo(f"Found {len(posts)} posts. Scanning for contact info...\n")

    added = 0
    duplicates = 0
    skipped = 0
    errors = 0
    processed_this_run = 0

    with tqdm(total=len(posts), desc="Processing", unit="posts") as pbar:
        for post in posts:
            post_id = post.get("id", "")
            if post_id in completed_ids:
                pbar.update(1)
                continue

            processed_this_run += 1

            success, msg = extractor.ingest_post(
                post=post,
                source="reddit",
                business_category=category,
                require_email_and_phone=require_email_and_phone,
            )

            if success:
                added += 1
                click.echo(f"  + {msg}")
            elif "Duplicate" in msg:
                duplicates += 1
            elif "No contact info" in msg:
                skipped += 1
            else:
                errors += 1
                click.echo(f"  ✗ {msg}")

            completed_ids.append(post_id)
            checkpoint_service.save_progress(
                "reddit", job_id, completed_ids, [], "running"
            )
            pbar.update(1)

    checkpoint_service.clear_checkpoint("reddit", job_id)

    click.echo(f"\n{'=' * 50}")
    click.echo(f"REDDIT SEARCH COMPLETE")
    click.echo(f"{'=' * 50}")
    click.echo(f"Posts processed (this run): {processed_this_run}")
    click.echo(f"Posts skipped (from checkpoint): {len(posts) - processed_this_run}")
    click.echo(f"New leads added: {added}")
    click.echo(f"Duplicates skipped: {duplicates}")
    click.echo(f"No contact info: {skipped}")
    click.echo(f"Errors: {errors}")
    click.echo(f"{'=' * 50}")
