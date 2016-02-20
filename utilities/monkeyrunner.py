import sys
import subprocess
from optparse import OptionParser

# jython imports
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice


def get_ip(device):
    print('Getting Device ip ...')
    result = device.shell('netcfg')
    ip_line = result.split('\n')[0]
    ip = ip_line.split()[2]
    ip = ip.split("/")[0]
    return ip


def launch_lite_serv(target_device, apk_path):

    print('Installing LiteServ on port 5984 ...')

    device = MonkeyRunner.waitForConnection(timeout=10, deviceId=target_device)
    success = device.installPackage(apk_path)
    if success:
        print('LiteServ install successful!')
    else:
        print('Could not install LiteServ!')
        sys.exit(1)

    print('Launching LiteServ activity ... ')
    device.shell('am start -a android.intent.action.MAIN -n com.couchbase.liteservandroid/com.couchbase.liteservandroid.MainActivity --ei listen_port 5984 --es username "" --es password ""')


def launch_android_app(target_device, apk_path, activity):

    print('Waiting for device "%s" ' % target_device)
    device = MonkeyRunner.waitForConnection(timeout=10, deviceId=target_device)

    print('Installing "%s" on device "%s" ' % (apk_path, target_device))
    success = device.installPackage(apk_path)
    if not success:
        print('Failed to install apk. Exiting!')
        sys.exit(1)

    print('Launching activity: "%s"' % activity)
    device.startActivity(component=activity)


def parse_args():
    """
    Parse command line args and return a tuple
    """
    parser = OptionParser()
    parser.add_option('', '--target-device', help="Device name from 'adb devices -l'", dest="target_device")
    parser.add_option('', '--local-port', help="Local port to forward listener to", type="int", dest="local_port")
    parser.add_option('', '--apk-path', help="Path to apk relative to repo root", dest="apk_path")
    parser.add_option('', '--activity', help="Activity manager activity path", dest="activity")
    (opts, args) = parser.parse_args()
    return parser, opts.target_device, opts.local_port, opts.apk_path, opts.activity


def validate_args(parser, target_device, local_port, apk_path, package_name):
    """
    Make sure all required args are passed, or else print usage
    """
    if target_device is None:
        parser.print_help()
        exit(-1)
    if local_port is None:
        parser.print_help()
        exit(-1)
    if apk_path is None:
        parser.print_help()
        exit(-1)
    if package_name is None:
        parser.print_help()
        exit(-1)

if __name__ == '__main__':

    parser, target_device, local_port, apk_path, activity = parse_args()
    validate_args(parser, target_device, local_port, apk_path, activity)

    if apk_path.endswith('couchbase-lite-android-liteserv-debug.apk'):
        ip = launch_lite_serv(target_device, apk_path)
    else:
        ip = launch_android_app(target_device, apk_path, activity)

    # print('Listing forwarded ports ...')
    # subprocess.check_call(['adb', '-s', target_device, 'forward', '--list'])
    # print('Clearing any forwarded ports ...')
    # subprocess.call(['adb', '-s', target_device, 'forward', '--remove-all'])
    print('Forwarding %s :5984 to localhost:%s' % (target_device, local_port))
    subprocess.call(['adb', '-s', target_device, 'forward', 'tcp:%d' % local_port, 'tcp:5984'])

