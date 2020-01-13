from ..core.module import Module # Base class for all modules
from ..core.types import StringType, ListType, ImageType, StructType, UrlType # This are some example types you can use
from ..core.elements import VariableSelector, VariableCreator, Selector, JSONOutput # The are some example UI elements you can use
from app.services.secret_service import SecretService

import requests
from random import randint

class Giphy( Module ):
    def setup( self ):
        self.metadata = {
            'name'            : 'giphy',
            'display-name'    : 'Giphy',
            'description'     : 'GIPHY is your top source for the best & newest GIFs & Animated Stickers online. ' + \
                                'Find everything from funny GIFs, reaction GIFs, unique GIFs and more.',
            'color'           : '#000000',
            'font-color'      : 'white',
            'documentation'   : 'https://docs.wayscript.com/library/modules/giphy',
            'google-connector': 'wayscript-giphy',
            'contributed-by'  : 'your_username',
        }

        self.add_setting( Selector( name = 'mode', display_name = 'Mode',
                          values = [ 'random_result', 'all_results' ],
                          default = 'random_result',
                          display_values = [ 'Single Random Result', 'All Results' ],
                          description = ( 'Single Random Result returns a single random result each time.<br><br>' +
                                          'All Results returns the top 25 results.' ) ) )

        self.add_input( VariableSelector( 'search_term', 'Search Term',
                                          StringType(), default = '', required = True ) )

        self.add_output( VariableCreator( 'gif', 'Gif', 
                            StructType( {  
                                'title'  : StringType(),
                                'url'    : UrlType(),
                                'img'    : ImageType( 'img' ),
                                'rating' : StringType(),
                                'id'     : StringType(),
                            } ) 
                       ) )

        self.add_output( VariableCreator( 'gif_list', 'Gifs',  
                            ListType( StructType( {
                                'title'  : StringType(),
                                'url'    : UrlType(),
                                'img'    : ImageType( 'img' ),
                                'rating' : StringType(),
                                'id'     : StringType(),
                            } ) )
                       ) )

        self.add_output( JSONOutput( 'output_json' ) )

    def get_api_key( self ):
        '''API Key must be provided to WayScript separately'''
        return SecretService().get_secret( SecretService.GIPHY )

    def setting_changed( self, setting, old_value, new_value ):
        '''
        You can use setting_changed to hide and show different elements. 
        It is called everytime a setting is changed and is passed the name of the setting
        that changed, its old value, and its new value.   
        '''
        if setting == 'mode':
            if new_value == 'random_result':
                self.outputs[ 'gif' ].show()
                self.outputs[ 'gif_list' ].hide()
            else:
                self.outputs[ 'gif' ].hide()
                self.outputs[ 'gif_list' ].show()

    def pull_attributes( self, res ):
        gif_id = res.get( 'id', '' )
        embed_url = f'https://media.giphy.com/media/{gif_id}/giphy.gif' if gif_id else ''
        img       = f'<img src="{embed_url}"/>'

        gif = {
            'title'  : res.get( 'title', '' ),
            'url'    : embed_url,
            'img'    : img,
            'rating' : res.get( 'rating', '' ),
            'id'     : gif_id,
        }
        return gif

    def get_random_int( self, results ):
        return randint( 0, len( results ) - 1 )

    def action( self ):
        '''This is where your script logic goes'''

        api_key = self.get_api_key()
        search_term = self.inputs[ 'search_term' ].get_value()

        if not search_term:
            if self.is_running_program():
                self.display_while_running( f'Search Term Required', message_type = 'warning' )
            return

        url = 'https://api.giphy.com/v1/gifs/search'        
        params = { 'api_key' : api_key, 
                   'q'       : search_term, 
                   'lang'    : 'en' }

        self.display_while_running( f'Pulling GIFs for {search_term}' )
        
        if self.test_mode():
            res_json = self.get_dummy_data( 'giphy' )
        else:
            r = requests.get( url, params = params )
            res_json = r.json()

        self.outputs[ 'output_json' ].set_value( res_json )

        results = res_json.get( 'data', [] )

        if not results:
            self.display_while_running( f'No GIFs found for {search_term}' )
            return

        if self.settings[ 'mode' ].get_value() == 'random_result':
            i = self.get_random_int( results )
            res = results[ i ]    
            gif = self.pull_attributes( res )
            self.outputs[ 'gif' ].set_value( gif )

        else: 
            gifs = []        
            for res in results:
                gif = self.pull_attributes( res )
                gifs.append( gif )

            self.outputs[ 'gif_list' ].set_value( gifs )
