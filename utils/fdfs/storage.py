from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FDFSStorage(Storage):

    def __init__(self, client_conf=None, base_url=None):
        '''初始化'''
        self.client_conf = client_conf if client_conf else settings.FDFS_CLIENT_CONF
        self.base_url = base_url if base_url else settings.FDFS_URL

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        """保存文件时使用"""
        # name：上传文件的名字
        # content：包含上传文件内容的file对象

        # 创建一个Fdfs_client对象
        client = Fdfs_client("./utils/fdfs/client.conf")

        res = client.upload_appender_by_buffer(content.read())
        '''
        @return dict {
            'Group name'      : group_name,
            'Remote file_id'  : remote_file_id,
            'Status'          : 'Upload successed.',
            'Local file name' : '',
            'Uploaded size'   : upload_size,
            'Storage IP'      : storage_ip
        } if success else None
        '''
        if res.get('Status') != 'Upload successed.':
            # 上传失败
            raise Exception('上传文件到fastdfs失败')

        # 获取返回的文件ID
        filename = res.get('Remote file_id')

        return filename

    def exists(self, name):
        '''Django判断文件名是否可用'''
        return False

    def url(self, name):
        '''返回访问文件的url路径'''
        return self.base_url + name
