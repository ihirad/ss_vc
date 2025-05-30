import subprocess

def git_add_and_commit(file_path, work_id, task_name):
    branch_name = f"{work_id}/{task_name.replace(' ', '_').lower()}"
    commit_message = f"{work_id}: Update print_diff for {task_name}"

    try:
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        subprocess.run(["git", "add", file_path], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e}")
