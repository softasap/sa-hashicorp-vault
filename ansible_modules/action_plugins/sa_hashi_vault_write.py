from __future__ import (absolute_import, division, print_function)
import os
from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase

__metaclass__ = type

ANSIBLE_HASHI_VAULT_ADDR = 'http://127.0.0.1:8200'

if os.getenv('VAULT_ADDR') is not None:
    ANSIBLE_HASHI_VAULT_ADDR = os.environ['VAULT_ADDR']

if os.getenv('VAULT_TOKEN') is not None:
    ANSIBLE_HASHI_VAULT_TOKEN = os.environ['VAULT_TOKEN']


class SaHashiVaultWrite:
    def __init__(self, **kwargs):
        try:
            import hvac
        except ImportError:
            AnsibleError("Please pip install hvac to use this module")

        self.url = kwargs.get('url', ANSIBLE_HASHI_VAULT_ADDR)

        self.token = kwargs.get('token', ANSIBLE_HASHI_VAULT_TOKEN)
        if self.token is None:
            raise AnsibleError("No Vault Token specified")

        self.value = kwargs.get('value', None)
        if self.value is None:
            raise AnsibleError("No Vault Value to write specified")

        # split secret arg, which has format 'secret/hello:value'
        # into secret='secret/hello' and secret_field='value'
        s = kwargs.get('secret')
        if s is None:
            raise AnsibleError("No secret specified")

        s_f = s.split(':')
        self.secret = s_f[0]
        if len(s_f) >= 2:
            self.secret_field = s_f[1]
        else:
            self.secret_field = 'value'

        self.client = hvac.Client(url=self.url, token=self.token)

        if self.client.is_authenticated():
            pass
        else:
            raise AnsibleError("Invalid Hashicorp Vault Token Specified")

    def write(self):
        data = self.client.write(self.secret, self.value)
        if data is None:
            raise AnsibleError("The secret %s doesn't seem to write successfully"
                               % self.secret)

        return data


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        ''' handler for fetch operations '''
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        if self._play_context.check_mode:
            result['skipped'] = True
            result['msg'] = 'check mode not (yet) supported for this module'
            return result

        url = self._task.args.get('url', ANSIBLE_HASHI_VAULT_ADDR)
        token = self._task.args.get('token', ANSIBLE_HASHI_VAULT_TOKEN)
        secret = self._task.args.get('secret', None)
        value = self._task.args.get('value', None)

        vault_dict = {
          'url': url,
          'token': token,
          'secret': secret,
          'value': value
          }

        vault_conn = SaHashiVaultWrite(**vault_dict)

        ret = vault_conn.write()

        return ret
