# openeuler_openstack_action
Github Action for openEuler OpenStack SIG

## 1. RPM检查
Action：packge_status_check.yaml

每日检查OBS上OpenStack SIG项目的RPM构建情况，如有构建失败的情况，自动在gitee的openstack项目中创建issue，如果相关issue已经存在，则改为刷新issue内容。
