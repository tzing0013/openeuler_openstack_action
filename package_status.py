import os
import ast
import datetime
import re

import requests
import yaml


BRANCHS = [
    'openEuler:20.03:LTS:SP2:oepkg:openstack:queens',
    'openEuler:20.03:LTS:SP2:oepkg:openstack:rocky',
    'openEuler:20.03:LTS:SP2:oepkg:openstack:common',
    'openEuler:21.03:Epol',
    'openEuler:21.09:Epol',
]


OBS_PACKAGE_BUILD_RESULT_URL = 'https://build.openeuler.org/build/%(branch)s/_result'
GITEE_ISSUE_LIST_URL = 'https://gitee.com/api/v5/repos/openeuler/openstack/issues?state=open&labels=kind/obs-failed&sort=created&direction=desc&page=1&per_page=20'
GITEE_ISSUE_CREATE_URL = 'https://gitee.com/api/v5/repos/openeuler/issues'
GITEE_ISSUE_UPDATE_URL = 'https://gitee.com/api/v5/repos/{owner}/issues/%s'
SIG_PROJECT_URL = 'https://gitee.com/openeuler/community/raw/master/sig/sig-openstack/sig-info.yaml'
OBS_USER_NAME = os.environ.get('OBS_USER_NAME')
OBS_USER_PASSWORD = os.environ.get('OBS_USER_PASSWORD')
GITEE_USER_TOKEN = os.environ.get('GITEE_USER_TOKEN')


def get_openstack_sig_project():
    project_list = []
    sig_dict = yaml.safe_load(requests.get(SIG_PROJECT_URL).content.decode())
    for item in sig_dict['repositories']:
        project_list.append(item['repo'].split('/')[-1])
    return project_list


def check_status():
    white_list = get_openstack_sig_project()
    branch_session = requests.session()
    branch_session.auth = (OBS_USER_NAME, OBS_USER_PASSWORD)
    result = {}
    for branch in BRANCHS:
        sub_res = {}
        res = branch_session.get(OBS_PACKAGE_BUILD_RESULT_URL % {'branch': branch})
        res_content = res.content.decode().split('\n')
        for project_line in res_content:
            project_name = None
            if re.search(r"(?<=package=\")[a-zA-Z0-9-_\.]*", project_line):
                project_name = re.search(r"(?<=package=\")[a-zA-Z0-9-_\.]*", project_line).group()
            is_broken = re.search(r'(code="unresolvable")|(code="failed")', project_line)
            if project_name and project_name in white_list and is_broken:
                status = re.search(r"(?<=code=\")(unresolvable)|(failed)", project_line).group()
                if not sub_res.get(project_name):
                    sub_res[project_name] = status
        if sub_res:
            result[branch] = sub_res
    return result


def get_obs_issue():
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
    }
    issue_list = requests.get(GITEE_ISSUE_LIST_URL, headers=headers).content.decode()
    issue_list = ast.literal_eval(issue_list)
    if issue_list:
        return issue_list[0]['id']
    else:
        return None


def update_issue(issue_number, result_str):
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
    }
    body = {
        "access_token": GITEE_USER_TOKEN,
        "body":result_str,
    }
    requests.patch(GITEE_ISSUE_UPDATE_URL % issue_number, headers=headers, params=body)


def creat_issue(result_str):
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
    }
    body = {
        "access_token": GITEE_USER_TOKEN,
        "repo":"openstack",
        "title":"[CI] OBS Build Failed",
        "body":result_str,
        "labels":"kind/obs-failed",
        "assignee":"huangtianhua",
        "collaborators":"xiyuanwang"
    }
    response = requests.post(GITEE_ISSUE_CREATE_URL, headers=headers, params=body)
    if response.status_code != 201:
        raise Exception("Failed create gitee issue")


def create_or_update_issue(result_str):
    issue_number = get_obs_issue()
    if issue_number:
        update_issue(issue_number, result_str)
    else:
        create_issue(result_str)


def format_content(input_dict):
    output = ""
    today = datetime.datetime.now()
    for branch, project_info in input_dict.items():
        output += '## check date: %s-%s-%s\n' % (today.year, today.month, today.day)
        output += '## %s\n' % branch
        output += '    \n'
        for project_name, status in project_info.items():
            output += '    %s: %s\n' % (project_name, status)
    return output


def main():
    result = check_status()
    if result:
        result_str = format_content(result)
        create_or_update_issue(result_str)


main()
