import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  Text
} from '@chakra-ui/react'
import { FaPatreon } from 'react-icons/fa';
import { useAuth0 } from '@auth0/auth0-react';

export const CaptivePatron = (props) => {
  const { loginWithRedirect } = useAuth0();
  return (
    <Modal isOpen={props.disclosure.isOpen} onClose={props.disclosure.onClose}>
      <ModalOverlay bg='none'
        backdropFilter='auto'
        backdropInvert='10%'
        backdropBlur='10px'/>
      <ModalContent>
        <ModalHeader>💎 Subscription Required</ModalHeader><ModalCloseButton />
        <ModalBody>
          You must have Supporter membership or higher in order to use this feature.
        </ModalBody>
        <ModalFooter>
          <Button variant='ghost' colorScheme='red' mr={3} onClick={props.disclosure.onClose}>
            Cancel
          </Button>
          <Button 
            h={8}
            pt={0}
            as={'a'}
            bg={"#f96854"}
            rounded={"md"}
            href={"https://www.patreon.com/feverdreamsAI"}
            cursor={'pointer'}
            display={'inline-flex'}
            alignItems={'center'}
            justifyContent={'center'}
            _hover={{
              bg: '#f96854',
            }}
            target="_blank"
            >
            <FaPatreon/>
            <Text ml={2}>Become a Patron!</Text>
          </Button>
          {/* <Button colorScheme={"blue"} onClick={() => loginWithRedirect()} aria-label={`Log In`}>Log In</Button> */}
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};