from dateutil import tz
from datetime import timezone, datetime


def main():
    to_zone = tz.gettz()
    print('AREA: ', to_zone)
    a = datetime.now()
    print('a:', a)
    b = a.strftime('%Y-%m-%d %H:%M:%S.%f')
    print('b: ', b, '; typeof(b): ', type(b))
    c = a.replace(tzinfo=timezone.utc)
    print('c:', c)
    d = a.replace(tzinfo=to_zone)
    print('d:', d)
    e = d.replace(tzinfo=timezone.utc)
    print('e:', e)
    f = c.utcfromtimestamp(c.timestamp()).strftime('%Y-%m-%d %H:%M:%S.%f')
    print('f:', f)
    g = d.utcfromtimestamp(d.timestamp()).strftime('%Y-%m-%d %H:%M:%S.%f')
    print('g:', g)
    h = d.strftime('%Y-%m-%d %H:%M:%S.%f')
    print('h:', h)
# this means that if this script is executed, then
# main() will be executed
if __name__ == '__main__':
    main()