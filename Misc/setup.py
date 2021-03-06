def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config=Configuration('Misc',parent_package,top_path)
    config.add_subpackage('test')
    config.add_extension('fkron',['fkron.f90'])
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(configuration=configuration)
