<?php

	class mod_remote extends atkModule
	{
	    function getNodes()
	    {
	      registerNode("remote.secure",array("admin","add","edit","delete","lock","unlock", "any_user", "any_project"));
	      registerNode("remote.timereg",array("admin","add","edit","delete","lock","unlock", "any_user", "any_project"));
	      registerNode("remote.timereport",array("admin","add","edit","delete","lock","unlock", "any_user", "any_project"));
	      registerNode("remote.query",array("admin","add","edit","delete","lock","unlock", "any_user", "any_project"));	    }  
		function getDependencies($mode)
		{
			return array("timestats");
		}
	    function getMenuItems()
	    {
	      $this->menuitem("remote",
	                      dispatch_url("remote.secure", "admin"),
	                      "main",true,370);
	      $this->menuitem("remote",
	                      dispatch_url("remote.timereport", "admin"),
	                      "main");
	    }
	}

?>
