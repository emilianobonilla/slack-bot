"""
Plugin loader for dynamically loading and managing Slack bot plugins.
"""
import os
import yaml
import importlib
import logging
from typing import Dict, Any, List, Optional
from plugins.base import BasePlugin, PluginResponse

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Loads and manages plugins for the Slack bot.
    """
    
    def __init__(self, config_path: str = "plugins.yaml"):
        """
        Initialize plugin loader.
        
        Args:
            config_path: Path to plugin configuration YAML file
        """
        self.config_path = config_path
        self.plugins: List[BasePlugin] = []
        self.global_config: Dict[str, Any] = {}
        self._loaded = False
    
    def load_plugins(self) -> None:
        """Load all enabled plugins from configuration."""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            self.global_config = config.get('global_config', {})
            plugin_configs = config.get('plugins', [])
            
            logger.info(f"Loading {len(plugin_configs)} plugin configurations")
            
            for plugin_config in plugin_configs:
                if not plugin_config.get('enabled', True):
                    logger.info(f"Skipping disabled plugin: {plugin_config.get('name')}")
                    continue
                
                try:
                    plugin = self._load_plugin(plugin_config)
                    if plugin:
                        self.plugins.append(plugin)
                        logger.info(f"Successfully loaded plugin: {plugin.name}")
                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_config.get('name')}: {e}")
            
            self._loaded = True
            logger.info(f"Plugin loader initialized with {len(self.plugins)} active plugins")
            
        except FileNotFoundError:
            logger.error(f"Plugin configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing plugin configuration: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading plugins: {e}")
            raise
    
    def _load_plugin(self, config: Dict[str, Any]) -> Optional[BasePlugin]:
        """
        Load a single plugin from configuration.
        
        Args:
            config: Plugin configuration dictionary
            
        Returns:
            Loaded plugin instance or None if failed
        """
        module_name = config.get('module')
        if not module_name:
            logger.error(f"No module specified for plugin: {config.get('name')}")
            return None
        
        try:
            # Import the plugin module
            module = importlib.import_module(module_name)
            
            # Look for plugin class (assumes class name matches module name)
            plugin_class_name = module_name.split('.')[-1].title() + 'Plugin'
            
            if hasattr(module, plugin_class_name):
                plugin_class = getattr(module, plugin_class_name)
            elif hasattr(module, 'Plugin'):
                plugin_class = getattr(module, 'Plugin')
            else:
                # Try to find any class that inherits from BasePlugin
                plugin_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BasePlugin) and 
                        attr is not BasePlugin):
                        plugin_class = attr
                        break
                
                if not plugin_class:
                    logger.error(f"No plugin class found in module: {module_name}")
                    return None
            
            # Create plugin instance
            plugin_instance = plugin_class(config)
            return plugin_instance
            
        except ImportError as e:
            logger.error(f"Failed to import plugin module {module_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error instantiating plugin {module_name}: {e}")
            return None
    
    def find_plugin_for_message(self, message_text: str) -> Optional[BasePlugin]:
        """
        Find the first plugin that can handle the given message.
        
        Args:
            message_text: The message text to match against
            
        Returns:
            Plugin that can handle the message, or None
        """
        if not self._loaded:
            logger.warning("Plugins not loaded, call load_plugins() first")
            return None
        
        # Remove bot mention from message for pattern matching
        clean_message = self._clean_message_text(message_text)
        
        for plugin in self.plugins:
            matched_text = plugin.can_handle(clean_message)
            if matched_text:
                logger.info(f"Plugin {plugin.name} matched text: '{matched_text}'")
                return plugin
        
        logger.debug(f"No plugin found for message: '{clean_message}'")
        return None
    
    def _clean_message_text(self, message_text: str) -> str:
        """
        Clean message text by removing bot mentions.
        
        Args:
            message_text: Original message text
            
        Returns:
            Cleaned message text
        """
        import re
        # Remove bot mentions like <@U1234567890>
        cleaned = re.sub(r'<@[A-Z0-9]+>', '', message_text)
        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())
        return cleaned.strip()
    
    def process_message(self, event_data: Dict[str, Any]) -> Optional[PluginResponse]:
        """
        Process a message through the appropriate plugin.
        
        Args:
            event_data: Full Slack event data
            
        Returns:
            Plugin response or None
        """
        # Support both direct text and nested event structure
        message_text = event_data.get('text', '') or event_data.get('event', {}).get('text', '')
        plugin = self.find_plugin_for_message(message_text)
        
        if not plugin:
            logger.info("No plugin found for message, using default response")
            return self._default_response(event_data)
        
        try:
            clean_message = self._clean_message_text(message_text)
            matched_text = plugin.can_handle(clean_message)
            
            logger.info(f"Processing message with plugin: {plugin.name}")
            response = plugin.process(event_data, matched_text)
            
            if response:
                logger.info(f"Plugin {plugin.name} generated response")
                return response
            else:
                logger.info(f"Plugin {plugin.name} processed message but returned no response")
                return None
                
        except Exception as e:
            logger.error(f"Error processing message with plugin {plugin.name}: {e}")
            # Return error response
            return PluginResponse(
                text=f"⚠️ Error procesando comando: {str(e)}",
                response_type="channel"
            )
    
    def _default_response(self, event_data: Dict[str, Any]) -> PluginResponse:
        """
        Generate default response when no plugin matches.
        
        Args:
            event_data: Slack event data
            
        Returns:
            Default plugin response
        """
        # Support both direct user_id and nested event structure
        user_id = event_data.get('user_id', '') or event_data.get('event', {}).get('user', '')
        return PluginResponse(
            text=f"¡Hola <@{user_id}>! No entendí ese comando. Usa `@bot help` para ver los comandos disponibles.",
            response_type="channel"
        )
    
    def get_available_plugins(self) -> List[Dict[str, str]]:
        """
        Get list of available plugins with their descriptions.
        
        Returns:
            List of plugin info dictionaries
        """
        return [
            {
                "name": plugin.name,
                "patterns": plugin.patterns,
                "description": getattr(plugin, 'description', plugin.get_help_text()),
                "help": plugin.get_help_text()
            }
            for plugin in self.plugins
        ]
    
    def reload_plugins(self) -> None:
        """Reload all plugins from configuration."""
        logger.info("Reloading plugins...")
        self.plugins.clear()
        self._loaded = False
        self.load_plugins()


# Global plugin loader instance
plugin_loader = PluginLoader()
